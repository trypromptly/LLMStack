import argparse
import logging
import os
import subprocess
from concurrent import futures
from typing import Iterator

import redis
from grpc import ServicerContext
from grpc import server as grpc_server
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from llmstack.common.runner.code_interpreter import CodeInterpreter
from llmstack.common.runner.display import VirtualDisplayPool
from llmstack.common.runner.playwright.browser import Playwright
from llmstack.common.runner.proto.runner_pb2 import (
    PlaywrightBrowserRequest,
    PlaywrightBrowserResponse,
    RemoteBrowserRequest,
    RemoteBrowserResponse,
    RestrictedPythonCodeRunnerRequest,
    RestrictedPythonCodeRunnerResponse,
)
from llmstack.common.runner.proto.runner_pb2_grpc import (
    RunnerServicer,
    add_RunnerServicer_to_server,
)
from llmstack.common.runner.remote_browser import RemoteBrowser

logger = logging.getLogger(__name__)


class Runner(RunnerServicer):
    def __init__(
        self, display_pool: VirtualDisplayPool = None, wss_secure=False, wss_hostname="localhost", wss_port=23100
    ):
        super().__init__()
        self.display_pool = display_pool
        self.wss_secure = wss_secure
        self.wss_hostname = wss_hostname
        self.wss_port = wss_port

        self.playwright = Playwright(display_pool)
        self.remote_browser = RemoteBrowser(display_pool, wss_secure, wss_hostname, wss_port)
        self.code_interpreter = CodeInterpreter()

    def GetPlaywrightBrowser(
        self,
        request_iterator: Iterator[PlaywrightBrowserRequest],
        context: ServicerContext,
    ) -> Iterator[PlaywrightBrowserResponse]:
        return self.playwright.get_browser(request_iterator=request_iterator)

    def GetRemoteBrowser(
        self,
        request_iterator: Iterator[RemoteBrowserRequest],
        context: ServicerContext,
    ) -> Iterator[RemoteBrowserResponse]:
        return self.remote_browser.get_remote_browser(request_iterator=request_iterator, context=context)

    def GetRestrictedPythonCodeRunner(
        self, request: RestrictedPythonCodeRunnerRequest, context: ServicerContext
    ) -> Iterator[RestrictedPythonCodeRunnerResponse]:
        return self.code_interpreter.get_restricted_python_code_runner(request=request, context=context)


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
    runner = Runner(
        display_pool=display_pool, wss_secure=args.wss_secure, wss_hostname=args.wss_hostname, wss_port=args.wss_port
    )

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
