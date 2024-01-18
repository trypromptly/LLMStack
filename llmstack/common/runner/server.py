import argparse
import asyncio
import json
import logging
import os
import re
import subprocess
import time
from concurrent import futures
from typing import Iterator

import matplotlib.pyplot as plt
import redis
from grpc import ServicerContext
from grpc import server as grpc_server
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from playwright._impl._api_types import TimeoutError
from playwright.async_api import async_playwright

from llmstack.common.runner.display import VirtualDisplayPool
from llmstack.common.runner.playwright.browser import Playwright
from llmstack.common.runner.proto.runner_pb2 import (
    TERMINATE,
    Content,
    ContentMimeType,
    PlaywrightBrowserRequest,
    PlaywrightBrowserResponse,
    RemoteBrowserRequest,
    RemoteBrowserResponse,
    RemoteBrowserSession,
    RemoteBrowserState,
    RestrictedPythonCodeRunnerRequest,
    RestrictedPythonCodeRunnerResponse,
)
from llmstack.common.runner.proto.runner_pb2_grpc import (
    RunnerServicer,
    add_RunnerServicer_to_server,
)

logger = logging.getLogger(__name__)


class Runner(RunnerServicer):
    def __init__(self, display_pool: VirtualDisplayPool = None):
        super().__init__()
        self.display_pool = display_pool
        self.playwright = Playwright(display_pool)

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
                browser = await playwright.chromium.launch(headless=False)
                context = await browser.new_context(no_viewport=True, storage_state=session_data)
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

    def GetRemoteBrowser(
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
                session_data=json.dumps(
                    session_state,
                )
                if session_state
                else "",
            ),
        )

    def GetPlaywrightBrowser(
        self,
        request_iterator: Iterator[PlaywrightBrowserRequest],
        context: ServicerContext,
    ) -> Iterator[PlaywrightBrowserResponse]:
        return self.playwright.get_browser(request_iterator=request_iterator)

    def GetRestrictedPythonCodeRunner(
        self, request: RestrictedPythonCodeRunnerRequest, context: ServicerContext
    ) -> Iterator[RestrictedPythonCodeRunnerResponse]:
        from google.protobuf.json_format import MessageToDict, ParseDict
        from google.protobuf.struct_pb2 import Struct, Value
        from RestrictedPython import compile_restricted
        from RestrictedPython.Guards import (
            guarded_iter_unpack_sequence,
            guarded_unpack_sequence,
            safe_builtins,
        )
        from RestrictedPython.transformer import IOPERATOR_TO_STR

        class CustomPrint(object):
            def __init__(self):
                self.enabled = True
                self.lines = []

            def write(self, text):
                if self.enabled:
                    if text and text.strip():
                        log_line = "{0}".format(text)
                        self.lines.append(
                            (
                                time.time(),
                                Content(data=bytes(log_line.encode("utf-8")), mime_type=ContentMimeType.TEXT),
                            )
                        )

            def enable(self):
                self.enabled = True

            def disable(self):
                self.enabled = False

            def __call__(self, *args):
                return self

            def _call_print(self, *objects, **kwargs):
                print(*objects, file=self)

        def custom_write(obj):
            """
            Custom hooks which controls the way objects/lists/tuples/dicts behave in
            RestrictedPython
            """
            return obj

        def custom_get_item(obj, key):
            return obj[key]

        def custom_get_iter(obj):
            return iter(obj)

        def custom_inplacevar(op, x, y):
            if op not in IOPERATOR_TO_STR.values():
                raise Exception("'{} is not supported inplace variable'".format(op))
            glb = {"x": x, "y": y}
            exec("x" + op + "y", glb)
            return glb["x"]

        async def execute_restricted_code(source_code, input_data={}):
            errors = None

            allowed_builtins = safe_builtins.copy()

            for builtin in []:
                allowed_builtins += (builtin,)

            mathplot_lib_display = []

            def custom_pyplot_show():
                import io

                from matplotlib.backends.backend_agg import (
                    FigureCanvasAgg as FigureCanvas,
                )

                # Save the current figure's buffer
                buf = io.BytesIO()

                # Use the current figure or create a new one
                fig = plt.gcf()

                # Create a canvas from the figure
                canvas = FigureCanvas(fig)

                # Draw the canvas and cache the renderer
                canvas.draw()

                # Save the figure to the buffer in PNG format
                fig.savefig(buf, format="png")

                # Release resources held by the figure
                plt.close(fig)

                # Rewind the buffer to start
                buf.seek(0)

                mathplot_lib_display.append((time.time(), Content(data=buf.read(), mime_type=ContentMimeType.PNG)))

                # Cleanup by closing the buffer
                buf.close()

            def custom_import(name, globals=None, locals=None, fromlist=(), level=0):
                module = __import__(name, globals, locals, fromlist, level)
                if module.__name__ == "matplotlib":
                    pyplot_attr = getattr(module, "pyplot")
                    if pyplot_attr and hasattr(pyplot_attr, "show"):
                        # Override pyplot.show() to route to our custom show function
                        pyplot_attr.show = custom_pyplot_show

                if fromlist:
                    safe_attrs = {attr: getattr(module, attr) for attr in fromlist}
                    if len(safe_attrs):
                        return type("RestrictedModule", (object,), safe_attrs)
                else:
                    return module

            custom_print = CustomPrint()
            code = compile_restricted(source_code, "<string>", "exec")
            builtins = allowed_builtins.copy()

            builtins["_write_"] = custom_write
            builtins["_print_"] = custom_print
            builtins["__import__"] = custom_import
            builtins["_getitem_"] = custom_get_item
            builtins["_getiter_"] = custom_get_iter
            builtins["_unpack_sequence_"] = guarded_unpack_sequence
            builtins["_iter_unpack_sequence_"] = guarded_iter_unpack_sequence
            builtins["_inplacevar_"] = custom_inplacevar
            builtins["_getattr_"] = getattr
            builtins["getattr"] = getattr
            builtins["_setattr_"] = setattr
            builtins["setattr"] = setattr

            restricted_globals = dict(__builtins__=builtins)
            local_variables = {**input_data}
            try:
                exec(code, restricted_globals, local_variables)
            except Exception as e:
                errors = f"error: {e}"

            local_variables = {
                k: v
                for k, v in local_variables.items()
                if isinstance(v, (int, float, str, bool, list, dict, tuple, type(None), Value, Struct))
            }
            # Return the result and any printed output
            return (
                local_variables,
                [x[1] for x in sorted(custom_print.lines + mathplot_lib_display, key=lambda x: x[0])],
                errors,
            )

        yield RestrictedPythonCodeRunnerResponse(state=RemoteBrowserState.RUNNING)

        with futures.ThreadPoolExecutor() as executor:

            def run_async_code(loop):
                asyncio.set_event_loop(loop)
                return loop.run_until_complete(
                    execute_restricted_code(
                        request.source_code, MessageToDict(request.input_data) if request.input_data else {}
                    )
                )

            # Create a new event loop that will be run in a separate thread
            new_loop = asyncio.new_event_loop()
            # Submit the function to the executor and get a Future object
            future = executor.submit(run_async_code, new_loop)
            # Wait for the future to complete and get the return value
            try:
                result, stdout, stderr = future.result(
                    timeout=min(request.timeout_secs if request.timeout_secs else 30, 30)
                )

            except Exception as e:
                logger.error(e)
                result, stdout, stderr = None, [], str(e)

        response = RestrictedPythonCodeRunnerResponse(
            exit_code=0,
            stdout=stdout,
            stderr=stderr,
            local_variables=ParseDict(result, Struct())
            if (result and isinstance(result, dict) and len(result.keys()) > 0)
            else None,
            state=RemoteBrowserState.TERMINATED,
        )

        yield response


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="LLMStack runner service")
    parser.add_argument(
        "--port",
        type=int,
        help="Port to run the server on",
        default=50051,
    )
    parser.add_argument(
        "--host",
        type=str,
        help="Host to run the server on",
        default="0.0.0.0",
    )
    parser.add_argument(
        "--max-displays",
        type=int,
        help="Maximum number of virtual displays to use",
        default=5,
    )
    parser.add_argument(
        "--start-display",
        type=int,
        help="Start display number number",
        default=99,
    )
    parser.add_argument(
        "--display-res",
        type=str,
        help="Display resolution",
        default="1024x720x24",
    )
    parser.add_argument(
        "--rfb-start-port",
        type=int,
        help="RFB start port",
        default=12000,
    )
    parser.add_argument(
        "--redis-host",
        type=str,
        help="Redis host",
        default="localhost",
    )
    parser.add_argument(
        "--redis-port",
        type=int,
        help="Redis port",
        default=6379,
    )
    parser.add_argument(
        "--redis-db",
        type=int,
        help="Redis DB",
        default=0,
    )
    parser.add_argument(
        "--redis-password",
        type=str,
        help="Redis password",
        default=None,
    )
    parser.add_argument(
        "--hostname",
        type=str,
        help="Hostname for mapping remote browser",
        default="localhost",
    )
    parser.add_argument(
        "--wss-hostname",
        type=str,
        help="Hostname for remote browser websocket",
        default="localhost",
    )
    parser.add_argument(
        "--wss-port",
        type=int,
        help="Port for remote browser websocket",
        default=23100,
    )
    parser.add_argument(
        "--wss-secure",
        type=bool,
        default=False,
        help="Secure remote browser websocket",
        action=argparse.BooleanOptionalAction,
    )
    parser.add_argument(
        "--playwright-port",
        type=int,
        help="Port for playwright server. Disabled by default",
        default=-1,
    )
    parser.add_argument
    parser.add_argument(
        "--log-level",
        type=str,
        help="Log level",
        default="INFO",
    )
    args = parser.parse_args()

    # Read environment variables and override arguments
    args.port = int(os.getenv("RUNNER_PORT", args.port))
    args.host = os.getenv("RUNNER_HOST", args.host)
    args.max_displays = int(
        os.getenv("RUNNER_MAX_DISPLAYS", args.max_displays),
    )
    args.start_display = int(
        os.getenv("RUNNER_START_DISPLAY", args.start_display),
    )
    args.display_res = os.getenv("RUNNER_DISPLAY_RES", args.display_res)
    args.rfb_start_port = int(
        os.getenv("RUNNER_RFB_START_PORT", args.rfb_start_port),
    )
    args.redis_host = os.getenv("RUNNER_REDIS_HOST", args.redis_host)
    args.redis_port = int(os.getenv("RUNNER_REDIS_PORT", args.redis_port))
    args.redis_password = os.getenv(
        "RUNNER_REDIS_PASSWORD",
        args.redis_password,
    )
    args.redis_db = int(os.getenv("RUNNER_REDIS_DB", args.redis_db))
    args.hostname = os.getenv("RUNNER_HOSTNAME", args.hostname)
    args.wss_hostname = os.getenv("RUNNER_WSS_HOSTNAME", args.wss_hostname)
    args.wss_port = int(os.getenv("RUNNER_WSS_PORT", args.wss_port))
    args.wss_secure = os.getenv("RUNNER_WSS_SECURE", args.wss_secure)
    args.log_level = os.getenv("RUNNER_LOG_LEVEL", args.log_level)
    args.playwright_port = int(
        os.getenv("RUNNER_PLAYWRIGHT_PORT", args.playwright_port),
    )

    # Configure logger
    logging.basicConfig(level=args.log_level)

    # Connect and verify redis
    redis_client = redis.Redis(
        host=args.redis_host,
        port=args.redis_port,
        db=args.redis_db,
        password=args.redis_password,
    )
    redis_client.ping()

    # Start playwright server if port is specified
    playwright_process = None
    if args.playwright_port > 0:
        playwright_process = subprocess.Popen(
            ["playwright", "run-server", "--port", str(args.playwright_port)],
        )

    display_pool = VirtualDisplayPool(
        redis_client,
        hostname=args.hostname,
        max_displays=args.max_displays,
        start_display=args.start_display,
        display_res=args.display_res,
        rfb_start_port=args.rfb_start_port,
    )

    # Start websockify server
    websockify_process = subprocess.Popen(
        [
            "websockify",
            f"{args.wss_port}",
            "--web",
            "/usr/share/www/html",
            "--token-plugin=llmstack.common.runner.token.TokenRedis",
            f'--token-source={args.redis_host}:{args.redis_port}:{args.redis_db}{f":{args.redis_password}" if args.redis_password else ""}',
            "-v",
            "--auth-plugin=llmstack.common.runner.auth.BasicHTTPAuthWithRedis",
            f'--auth-source={args.redis_host}:{args.redis_port}:{args.redis_db}{f":{args.redis_password}" if args.redis_password else ""}',
        ],
        close_fds=True,
    )

    server = grpc_server(
        futures.ThreadPoolExecutor(
            max_workers=10,
            thread_name_prefix="grpc_workers",
        ),
    )
    runner = Runner(display_pool=display_pool)
    runner.wss_hostname = args.wss_hostname
    runner.wss_port = args.wss_port
    runner.wss_secure = args.wss_secure

    add_RunnerServicer_to_server(runner, server)

    # Add health checking service
    health_servicer = health.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)

    # Set the health status to SERVING
    health_servicer.set("", health_pb2.HealthCheckResponse.SERVING)

    server.add_insecure_port(f"[::]:{args.port}")
    server.start()

    logger.info(f"Server running at http://[::]:{args.port}")
    server.wait_for_termination()

    # Stop websockify and playwright servers
    websockify_process.kill()
    playwright_process.kill()


if __name__ == "__main__":
    main()
