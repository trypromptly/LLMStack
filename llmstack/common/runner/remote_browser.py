import asyncio
import json
import logging
import os
import random
import re
from concurrent import futures
from typing import Iterator

from grpc import ServicerContext
from playwright.async_api import TimeoutError, async_playwright

from llmstack.common.runner.playwright.browser import BROWSER_INIT_SCRIPT, USER_AGENTS
from llmstack.common.runner.proto.runner_pb2 import (
    TERMINATE,
    RemoteBrowserRequest,
    RemoteBrowserResponse,
    RemoteBrowserSession,
    RemoteBrowserState,
)

logger = logging.getLogger(__name__)


class RemoteBrowser:
    def __init__(self, display_pool, wss_secure, wss_hostname, wss_port):
        self.display_pool = display_pool
        self.wss_secure = wss_secure
        self.wss_hostname = wss_hostname
        self.wss_port = wss_port

    async def _process_remote_browser_input_stream(
        self,
        request_iterator: Iterator[RemoteBrowserRequest],
        display,
        request: RemoteBrowserRequest,
    ):
        os.environ["DISPLAY"] = f'{display["DISPLAY"]}.0'
        logger.info(f"Using {os.environ['DISPLAY']}")
        session_data = None
        terminate = False
        async with async_playwright() as playwright:
            try:
                session_data = (
                    json.loads(
                        request.init_data.session_data,
                    )
                    if request.init_data.session_data
                    else None
                )
                browser = await playwright.chromium.launch(
                    headless=False, args=["--disable-blink-features=AutomationControlled"]
                )
                context = await browser.new_context(
                    no_viewport=True,
                    storage_state=session_data,
                    user_agent=USER_AGENTS[random.randint(0, len(USER_AGENTS) - 1)],
                )
                await context.add_init_script(BROWSER_INIT_SCRIPT)
                page = await context.new_page()

                # Create an async task for waiting for the URL pattern
                page_load_task = asyncio.create_task(
                    page.wait_for_url(
                        re.compile(
                            request.init_data.terminate_url_pattern or "chrome://newtab",
                        ),
                        timeout=request.init_data.timeout * 1000,
                    ),
                )

                # Navigate to the initial URL
                await page.goto(request.init_data.url or "chrome://newtab")

                for next_request in request_iterator:
                    if next_request is not None:
                        if next_request.input.type == TERMINATE:
                            logger.info(
                                "Terminating browser because of timeout",
                            )
                            page_load_task.cancel()
                            break
                    else:
                        # Sleep a bit to prevent a busy loop that consumes too
                        # much CPU
                        await asyncio.sleep(0.1)

                    if page_load_task.done():
                        break

                # Wait for the page load task to complete
                if not page_load_task.done():
                    await page_load_task

            except TimeoutError:
                pass
            except Exception as e:
                logger.exception(e)
                terminate = True
            finally:
                # Stop page load task if still running
                if not page_load_task.done():
                    page_load_task.cancel()

                if request.init_data.persist_session and (
                    page_load_task.done() or not request.init_data.terminate_url_pattern
                ):
                    session_data = await context.storage_state()

                # Clean up
                await context.close()
                await browser.close()

                if terminate:
                    raise Exception("Terminating browser")

                return session_data

    def get_remote_browser(
        self,
        request_iterator: Iterator[RemoteBrowserRequest],
        context: ServicerContext,
    ) -> Iterator[RemoteBrowserResponse]:
        # Get input from the client
        request = next(request_iterator)

        # Get a display from the pool and send its info to the client
        display = self.display_pool.get_display(remote_control=True)
        wss_server_path = f"{self.wss_hostname}:{self.wss_port}" if "/" not in self.wss_hostname else self.wss_hostname

        # Return the display info to the client
        yield RemoteBrowserResponse(
            session=RemoteBrowserSession(
                ws_url=f"{'wss' if self.wss_secure else 'ws'}://{display['username']}:{display['password']}@{wss_server_path}?token={display['token']}",
            ),
            state=RemoteBrowserState.RUNNING,
        )

        # Use ThreadPoolExecutor to run the async function in a separate thread
        with futures.ThreadPoolExecutor() as executor:
            # Wrap the coroutine in a function that gets the current event loop
            # or creates a new one
            def run_async_code(loop):
                asyncio.set_event_loop(loop)
                return loop.run_until_complete(
                    self._process_remote_browser_input_stream(
                        request_iterator,
                        display,
                        request,
                    ),
                )

            # Create a new event loop that will be run in a separate thread
            new_loop = asyncio.new_event_loop()
            # Submit the function to the executor and get a Future object
            future = executor.submit(run_async_code, new_loop)

            # Wait for the future to complete and get the return value
            try:
                session_state = future.result()
            except Exception as e:
                logger.error(e)
                session_state = None

        # Put the display back in the pool and return
        self.display_pool.put_display(display)
        yield RemoteBrowserResponse(
            state=RemoteBrowserState.TERMINATED,
            session=RemoteBrowserSession(
                session_data=(
                    json.dumps(
                        session_state,
                    )
                    if session_state
                    else ""
                ),
            ),
        )
