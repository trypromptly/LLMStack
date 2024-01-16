import asyncio
import logging
from typing import Iterator, Union

import grpc
from django.conf import settings
from pydantic import Field

from llmstack.common.blocks.base.schema import BaseSchema
from llmstack.common.runner.proto import runner_pb2, runner_pb2_grpc
from llmstack.connections.models import (
    Connection,
    ConnectionActivationInput,
    ConnectionActivationOutput,
    ConnectionStatus,
    ConnectionType,
)
from llmstack.connections.types import ConnectionTypeInterface

logger = logging.getLogger(__name__)


class WebLoginBaseConfiguration(BaseSchema):
    _storage_state: str = Field(
        description="Storage state",
        widget="textarea",
        hidden=True,
    )


class WebLoginConfiguration(WebLoginBaseConfiguration):
    start_url: str = Field(
        description="URL to login to",
        default="https://google.com",
    )


class WebLogin(ConnectionTypeInterface[WebLoginConfiguration]):
    @staticmethod
    def name() -> str:
        return "Web Login"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    @staticmethod
    def slug() -> str:
        return "web_login"

    @staticmethod
    def description() -> str:
        return "Login to a website"

    @staticmethod
    def type() -> ConnectionType:
        return ConnectionType.BROWSER_LOGIN

    def input(self, activation_input: ConnectionActivationInput) -> None:
        if activation_input.data == "terminate":
            self._is_terminated = True

    async def _request_iterator(self, connection, timeout):
        session_data = (
            connection.configuration["_storage_state"]
            if "_storage_state" in connection.configuration and connection.configuration["_storage_state"]
            else ""
        )
        yield runner_pb2.RemoteBrowserRequest(
            init_data=runner_pb2.BrowserInitData(
                url=connection.configuration["start_url"],
                terminate_url_pattern="",
                session_data=session_data,
                timeout=timeout,
                persist_session=True,
            ),
        )

        # Sleep till timeout or self._is_terminated is True
        time_elapsed = 0
        while not self._is_terminated and time_elapsed < timeout:
            await asyncio.sleep(0.1)
            time_elapsed += 0.1

        yield runner_pb2.RemoteBrowserRequest(input=runner_pb2.BrowserInput(type=runner_pb2.TERMINATE))

    async def _read_browser_output(self, connection, remote_browser_stream):
        while not self._is_terminated:
            try:
                # Read the next message from the stream
                output = await remote_browser_stream.read()
                if output.state is not runner_pb2.RemoteBrowserState.RUNNING:
                    self._is_terminated = True
                    if output.session.session_data:
                        connection.configuration["_storage_state"] = output.session.session_data
                        connection.status = ConnectionStatus.ACTIVE
                    else:
                        connection.status = ConnectionStatus.FAILED
                    break
            except grpc.aio.AioRpcError as e:
                # Handle the case where the stream has been closed by the
                # server
                if e.code() == grpc.StatusCode.CANCELLED:
                    # Stream has been cancelled, likely no more messages to
                    # read
                    logger.info("Stream was cancelled, no more messages.")
                    break
                else:
                    # An actual error occurred, log or re-raise
                    logger.error(
                        f"RPC error occurred: {e.code()} - {e.details()}",
                    )
                    raise
            except asyncio.CancelledError:
                # The task was cancelled, so exit the loop
                logger.info("Task was cancelled, exiting read loop.")
                break
            except TimeoutError:
                pass

            await asyncio.sleep(0.01)

        return connection

    async def activate(self, connection) -> Iterator[Union[Connection, dict]]:
        self.channel = grpc.aio.insecure_channel(
            f"{settings.RUNNER_HOST}:{settings.RUNNER_PORT}",
        )
        stub = runner_pb2_grpc.RunnerStub(self.channel)
        self._input_index = 0
        self._input_instructions = []
        self._is_terminated = False
        timeout = 120

        self.remote_browser_stream = stub.GetRemoteBrowser(
            self._request_iterator(connection, timeout),
        )

        first_message = await self.remote_browser_stream.read()

        ws_url = first_message.session.ws_url

        yield ConnectionActivationOutput(data={"ws_url": ws_url, "timeout": timeout})

        # Consume the stream in a separate task and return the connection
        connection = await self._read_browser_output(connection, self.remote_browser_stream)

        await self.channel.close()
        yield connection
