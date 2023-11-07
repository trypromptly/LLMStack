import asyncio
import logging
import os
import re
import subprocess
from concurrent import futures
from typing import Iterator

import redis
from grpc import ServicerContext
from grpc import server as grpc_server
from playwright._impl._api_types import TimeoutError
from playwright.async_api import async_playwright

from llmstack.common.runner.display import VirtualDisplayPool
from llmstack.common.runner.proto.runner_pb2 import (
    TERMINATE,
    RemoteBrowserRequest,
    RemoteBrowserResponse,
    RemoteBrowserSession,
    RemoteBrowserState,
)
from llmstack.common.runner.proto.runner_pb2_grpc import (
    RunnerServicer,
    add_RunnerServicer_to_server,
)

MAX_DISPLAYS = 5
START_DISPLAY = 99
RFB_START_PORT = 12000
WS_START_PORT = 23000
WSS_PORT = '23100'
HOSTNAME = 'localhost'
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

logger = logging.getLogger(__name__)


class Runner(RunnerServicer):
    def __init__(self, display_pool: VirtualDisplayPool = None):
        super().__init__()
        self.display_pool = display_pool

    async def _process_remote_browser_input_stream(self, request_iterator: Iterator[RemoteBrowserRequest], display, request: RemoteBrowserRequest):
        os.environ['DISPLAY'] = f'{display["DISPLAY"]}.0'
        logger.info(f"Using {os.environ['DISPLAY']}")
        session_data = None
        async with async_playwright() as playwright:
            try:
                browser = await playwright.chromium.launch(headless=False)
                context = await browser.new_context(no_viewport=True, storage_state=request.init_data.session_data or None)
                page = await context.new_page()

                # Create an async task for waiting for the URL pattern
                page_load_task = asyncio.create_task(
                    page.wait_for_url(
                        re.compile(
                            request.init_data.terminate_url_pattern or 'chrome://newtab'),
                        timeout=request.init_data.timeout*1000
                    )
                )

                # Navigate to the initial URL
                await page.goto(request.init_data.url or 'chrome://newtab')

                for next_request in request_iterator:
                    if next_request is not None:
                        if next_request.input.type == TERMINATE:
                            raise Exception(
                                'Terminating browser because of timeout')
                    else:
                        # Sleep a bit to prevent a busy loop that consumes too much CPU
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
            finally:
                # Stop page load task if still running
                if not page_load_task.done():
                    page_load_task.cancel()

                if request.init_data.persist_session and (page_load_task.done() or not request.init_data.terminate_url_pattern):
                    session_data = await context.storage_state()

                # Clean up
                await context.close()
                await browser.close()

        return session_data

    def GetRemoteBrowser(self, request_iterator: Iterator[RemoteBrowserRequest], context: ServicerContext) -> Iterator[RemoteBrowserResponse]:
        # Get input from the client
        request = next(request_iterator)

        # Get a display from the pool and send its info to the client
        display = self.display_pool.get_display(remote_control=True)

        # Return the display info to the client
        yield RemoteBrowserResponse(
            session=RemoteBrowserSession(
                ws_url=f"ws://{display['username']}:{display['password']}@localhost:{WSS_PORT}?token={display['token']}",
            ),
            state=RemoteBrowserState.RUNNING,
        )

        # Use ThreadPoolExecutor to run the async function in a separate thread
        with futures.ThreadPoolExecutor() as executor:
            # Wrap the coroutine in a function that gets the current event loop or creates a new one
            def run_async_code(loop):
                asyncio.set_event_loop(loop)
                return loop.run_until_complete(
                    self._process_remote_browser_input_stream(
                        request_iterator, display, request)
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
                session_data=str(session_state) if session_state else '',
            ),
        )


def main():
    # Configure logger
    logging.basicConfig(level=logging.INFO)

    # Connect and verify redis
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
    redis_client.ping()

    display_pool = VirtualDisplayPool(
        redis_client, hostname=HOSTNAME, max_displays=MAX_DISPLAYS, start_display=START_DISPLAY, display_res='1024x720x24', rfb_start_port=RFB_START_PORT)

    # Start websockify server
    websockify_process = subprocess.Popen(['websockify', WSS_PORT, '--token-plugin=TokenRedis', f'--token-source={REDIS_HOST}:{REDIS_PORT}',
                                          '-v', '--auth-plugin=llmstack.common.runner.auth.BasicHTTPAuthWithRedis', f'--auth-source={REDIS_HOST}:{REDIS_PORT}'], close_fds=True)

    server = grpc_server(futures.ThreadPoolExecutor(max_workers=10))
    runner = Runner(display_pool=display_pool)

    add_RunnerServicer_to_server(runner, server)
    server.add_insecure_port('[::]:50051')
    server.start()
    logger.info("Server running at http://0.0.0.0:50051")
    server.wait_for_termination()

    # Stop websockify server
    websockify_process.kill()


if __name__ == '__main__':
    main()
