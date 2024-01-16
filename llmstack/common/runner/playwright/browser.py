import asyncio
import json
import logging
import os
from concurrent import futures
from typing import Iterator

import ffmpeg
from playwright.async_api import Page, async_playwright

from llmstack.common.runner.proto import runner_pb2
from llmstack.common.runner.proto.runner_pb2 import (
    TERMINATE,
    BrowserButton,
    BrowserContent,
    BrowserInputField,
    BrowserLink,
    BrowserSelectField,
    BrowserTextAreaField,
    PlaywrightBrowserRequest,
    PlaywrightBrowserResponse,
    RemoteBrowserState,
)

logger = logging.getLogger(__name__)


class Playwright:
    def __init__(self, display_pool):
        self.display_pool = display_pool

        # Load utils script
        with open(os.path.join(os.path.dirname(__file__), "utils.js")) as f:
            self.utils_js = f.read()

    async def get_browser_content_from_page(self, page: Page, utils_js: str) -> BrowserContent:
        content = BrowserContent()

        try:
            content.url = page.url
            content.title = await page.title()

            # Load utils script
            await page.evaluate(utils_js)

            # Script to collect details of all elements and add bounding boxes
            # and labels
            page_details = await page.evaluate("addTags();")
            content.text = page_details["text"]

            # Process the returned data
            for button in page_details["buttons"]:
                content.buttons.append(
                    BrowserButton(
                        text=button["text"],
                        selector=button["tag"],
                    ),
                )

            # Include interactable labels and divs as buttons if clickable
            for label in page_details["labels"]:
                content.buttons.append(
                    BrowserButton(
                        text=label["text"],
                        selector=label["tag"],
                    ),
                )

            for div in page_details["divs"]:
                if div["clickable"]:
                    content.buttons.append(
                        BrowserButton(
                            text=div["text"],
                            selector=div["tag"],
                        ),
                    )

            for input in page_details["inputs"]:
                content.inputs.append(
                    BrowserInputField(
                        text=input["text"],
                        selector=input["tag"],
                    ),
                )

            for select in page_details["selects"]:
                content.selects.append(
                    BrowserSelectField(
                        text=select["text"],
                        selector=select["tag"],
                    ),
                )

            for textarea in page_details["textareas"]:
                content.textareas.append(
                    BrowserTextAreaField(
                        text=textarea["text"],
                        selector=textarea["tag"],
                    ),
                )

            # Add typable divs as textareas
            for div in page_details["divs"]:
                if div["editable"]:
                    content.textareas.append(
                        BrowserTextAreaField(
                            text=div["text"],
                            selector=div["tag"],
                        ),
                    )

            for link in page_details["links"]:
                content.links.append(
                    BrowserLink(
                        text=link["text"],
                        selector=link["tag"],
                        url=link["url"],
                    ),
                )

            # Add a screenshot
            content.screenshot = await page.screenshot(type="png")

            # Clear tags
            await page.evaluate("clearTags();")
        except Exception as e:
            logger.error(e)
            content.error = str(e)

        return content

    async def _process_playwright_request(self, page: Page, request):
        def _get_locator(page, selector):
            if (
                selector.startswith("a=")
                or selector.startswith("b=")
                or selector.startswith("in=")
                or selector.startswith(
                    "s=",
                )
                or selector.startswith("ta=")
                or selector.startswith("l=")
                or selector.startswith("d=")
            ):
                name, value = selector.split("=")
                if name == "in":
                    name = "input"
                elif name == "ta":
                    name = "textarea"
                elif name == "s":
                    name = "select"
                elif name == "b":
                    name = "button"
                elif name == "l":
                    name = "label"
                elif name == "d":
                    name = "div"

                return page.locator(name).nth(int(value))
            return page.locator(selector)

        steps = list(request.steps)
        outputs = []
        error = None
        logger.info(steps)
        terminated = False

        for step in steps:
            try:
                if step.type == TERMINATE:
                    terminated = True
                    raise Exception(
                        "Terminating browser because of timeout",
                    )
                elif step.type == runner_pb2.GOTO:
                    await page.goto(
                        (page.url + step.data if step.data and step.data.startswith("/") else step.data) or page.url,
                    )
                elif step.type == runner_pb2.CLICK:
                    locator = _get_locator(page, step.selector)
                    await locator.click(timeout=2000)
                    await page.wait_for_timeout(200)  # Wait
                elif step.type == runner_pb2.WAIT:
                    timeout = min(
                        int(step.data) * 1000 if step.data else 5000,
                        10000,
                    )
                    if not step.selector:
                        await page.wait_for_timeout(timeout)
                    else:
                        await page.wait_for_selector(step.selector, timeout=timeout)
                elif step.type == runner_pb2.COPY:
                    results = await page.query_selector_all(step.selector or "body")
                    outputs.append(
                        {
                            "url": page.url,
                            "text": "".join([await result.inner_text() for result in results]),
                        },
                    )
                elif step.type == runner_pb2.TYPE:
                    locator = _get_locator(page, step.selector)
                    # Clear before typing
                    await locator.fill("", timeout=1000)
                    await locator.press_sequentially(step.data, timeout=1000)
                elif step.type == runner_pb2.SCROLL_X:
                    await page.mouse.wheel(delta_x=int(step.data), delta_y=0)
                elif step.type == runner_pb2.SCROLL_Y:
                    await page.mouse.wheel(delta_x=0, delta_y=int(step.data))
                elif step.type == runner_pb2.ENTER:
                    if await page.evaluate(
                        '() => { return (document.activeElement.tagName === "INPUT" || document.activeElement.tagName === "TEXTAREA"); }',
                    ):
                        await page.keyboard.press("Enter")
                        # Wait for navigation to complete if any
                        await page.wait_for_timeout(5000)
            except Exception as e:
                logger.exception(e)
                error = str(e)
            finally:
                if terminated:
                    raise Exception("Terminating browser")

        return outputs, error

    async def _process_playwright_input_stream(self, initial_request, request_iterator, display, ffmpeg_process):
        os.environ["DISPLAY"] = f'{display["DISPLAY"]}.0'
        logger.info(f"Using {os.environ['DISPLAY']}")
        outputs = []
        content = BrowserContent()
        session_data = initial_request.session_data

        async with async_playwright() as playwright:
            try:
                session_data = (
                    json.loads(
                        session_data,
                    )
                    if session_data
                    else None
                )
                browser = await playwright.chromium.launch(headless=False)
                context = await browser.new_context(no_viewport=True, storage_state=session_data)
                page = await context.new_page()

                url = initial_request.url
                if not url.startswith("http"):
                    url = f"https://{url}"

                # Load the start_url before processing the steps
                await page.goto(url, wait_until="domcontentloaded")

                outputs, error = await self._process_playwright_request(
                    page,
                    initial_request,
                )
                content = await self.get_browser_content_from_page(page, self.utils_js)
                if error:
                    content.error = error

                yield (outputs, content)

                for next_request in request_iterator:
                    output, error = await self._process_playwright_request(
                        page,
                        next_request,
                    )
                    outputs += output

                    # Populate content from the last page
                    content = await self.get_browser_content_from_page(page, self.utils_js)
                    if error:
                        content.error = error

                    yield (outputs, content)

                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.exception(e)
            finally:
                # Clean up
                await browser.close()

                if ffmpeg_process:
                    # Wait for 5 seconds before killing ffmpeg
                    await asyncio.sleep(5)
                    ffmpeg_process.kill()

                yield (outputs, content)

    def get_browser(
        self,
        request_iterator: Iterator[PlaywrightBrowserRequest],
    ) -> Iterator[PlaywrightBrowserResponse]:
        # Get the first request from the client
        initial_request = next(request_iterator)
        display = self.display_pool.get_display(remote_control=False)
        SENTINAL = object()

        if not display:
            yield PlaywrightBrowserResponse(state=RemoteBrowserState.TERMINATED)
            return

        # Start ffmpeg in a separate process to stream the display
        ffmpeg_process = (
            ffmpeg.input(
                f"{display['DISPLAY']}.0",
                format="x11grab",
                framerate=10,
                video_size=(
                    1024,
                    720,
                ),
            )
            .output(
                "pipe:",
                format="mp4",
                vcodec="h264",
                movflags="faststart+frag_keyframe+empty_moov+default_base_moof",
                g=25,
                y=None,
            )
            .run_async(
                pipe_stdout=True,
                pipe_stderr=True,
            )
        )

        # Use ThreadPoolExecutor to run the async function in a separate thread
        with futures.ThreadPoolExecutor(thread_name_prefix="async_tasks") as executor:
            browser_done = False
            video_done = False
            # Wrap the coroutine in a function that gets the current event loop
            # or creates a new one

            def run_async_code(loop, fn):
                asyncio.set_event_loop(loop)

                return loop.run_until_complete(fn())

            # Create a queue to store the browser output
            content_queue = asyncio.Queue()

            # Create a queue to store browser video output
            video_queue = asyncio.Queue()

            async def collect_browser_content():
                async for (outputs, content) in self._process_playwright_input_stream(
                    initial_request,
                    request_iterator,
                    display,
                    ffmpeg_process,
                ):
                    await content_queue.put((outputs, content))
                await content_queue.put(SENTINAL)

            async def read_video_output():
                while True and ffmpeg_process:
                    try:
                        chunk = ffmpeg_process.stdout.read(1024 * 3)
                        if len(chunk) == 0:
                            break
                        await video_queue.put(chunk)
                    except Exception as e:
                        logger.error(e)
                        break
                await video_queue.put(SENTINAL)

            # Start a task to read the video output from ffmpeg
            video_future = executor.submit(
                run_async_code,
                asyncio.new_event_loop(),
                read_video_output,
            )

            # Submit the function to the executor and get a Future object
            content_future = executor.submit(
                run_async_code,
                asyncio.new_event_loop(),
                collect_browser_content,
            )

            # Wait for the future to complete and get the return value
            try:
                yield PlaywrightBrowserResponse(state=RemoteBrowserState.RUNNING)

                while not browser_done and not video_done:
                    try:
                        item = content_queue.get_nowait()
                        if item is SENTINAL:
                            browser_done = True
                            break

                        (output_texts, content) = item
                        response = PlaywrightBrowserResponse(
                            state=RemoteBrowserState.RUNNING,
                        )

                        for output_text in output_texts:
                            response.outputs.append(
                                runner_pb2.BrowserOutput(
                                    text=output_text["text"],
                                    url=output_text["url"],
                                ),
                            )
                        response.content.CopyFrom(content)

                        yield response
                    except asyncio.QueueEmpty:
                        pass

                    try:
                        chunk = video_queue.get_nowait()
                        if chunk is SENTINAL:
                            video_done = True
                            break
                        if initial_request.stream_video:
                            yield PlaywrightBrowserResponse(video=chunk)
                    except asyncio.QueueEmpty:
                        pass

                    if content_future.done() or video_future.done() or browser_done or video_done:
                        break

                # Check if we have any data left in the video queue
                while not video_queue.empty():
                    chunk = video_queue.get_nowait()
                    if chunk is SENTINAL:
                        video_done = True
                        break
                    if initial_request.stream_video:
                        yield PlaywrightBrowserResponse(video=chunk)

                yield PlaywrightBrowserResponse(
                    state=RemoteBrowserState.TERMINATED,
                )
            except Exception as e:
                logger.error(e)
                yield PlaywrightBrowserResponse(
                    state=RemoteBrowserState.TERMINATED,
                )
            finally:
                self.display_pool.put_display(display)
