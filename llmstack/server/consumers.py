import asyncio
import json
import logging
import uuid

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.http import HttpRequest, QueryDict

from llmstack.connections.actors import ConnectionActivationActor
from llmstack.connections.models import (
    Connection,
    ConnectionActivationInput,
    ConnectionActivationOutput,
    ConnectionStatus,
)

logger = logging.getLogger(__name__)


@database_sync_to_async
def _build_request_from_input(post_data, scope):
    headers = dict(scope["headers"])
    content_type = headers.get(
        b"content-type",
        b"application/json",
    ).decode("utf-8")
    path_info = scope.get("path", "")
    method = scope.get("method", "")
    query_string = scope.get("query_string", b"").decode("utf-8")
    query_params = QueryDict(query_string)
    user = scope.get("user")

    http_request = HttpRequest()
    http_request.META = {
        "CONTENT_TYPE": content_type,
        "PATH_INFO": path_info,
        "QUERY_STRING": query_string,
        "HTTP_USER_AGENT": headers.get(
            b"user-agent",
            b"",
        ).decode("utf-8"),
        "REMOTE_ADDR": headers.get(
            b"x-forwarded-for",
            b"",
        )
        .decode("utf-8")
        .split(",")[0]
        .strip(),
    }
    http_request.method = method
    http_request.GET = query_params
    http_request.stream = json.dumps(post_data)
    http_request.user = user
    http_request.data = post_data

    return http_request


class AppConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.app_id = self.scope["url_route"]["kwargs"]["app_id"]
        self.preview = True if "preview" in self.scope["url_route"]["kwargs"] else False
        self._session_id = None
        await self.accept()

    async def disconnect(self, close_code):
        # TODO: Close the stream
        pass

    async def _respond_to_event(self, text_data):
        from llmstack.apps.apis import AppViewSet

        json_data = json.loads(text_data)
        input = json_data.get("input", {})
        id = json_data.get("id", None)
        event = json_data.get("event", None)
        self._session_id = self._session_id or json_data.get(
            "session_id",
            None,
        )

        if event == "run":
            try:
                request_uuid = str(uuid.uuid4())
                request = await _build_request_from_input({"input": input, "stream": True}, self.scope)
                output_stream = await AppViewSet().run_app_internal_async(
                    self.app_id,
                    self._session_id,
                    request_uuid,
                    request,
                    self.preview,
                )
                # Generate a uuid for the response
                response_id = str(uuid.uuid4())

                async for output in output_stream:
                    if "errors" in output or "session" in output:
                        if "session" in output:
                            self._session_id = output["session"]["id"]
                        await self.send(text_data=json.dumps({**output, **{"reply_to": id}}))
                    else:
                        await self.send(text_data=json.dumps({"output": output, "reply_to": id, "id": response_id}))

                await self.send(text_data=json.dumps({"event": "done", "reply_to": id, "id": response_id}))
            except Exception as e:
                logger.exception(e)
                await self.send(text_data=json.dumps({"errors": [str(e)], "reply_to": id}))

        if event == "init":
            # Create a new session and return the session id
            self._session_id = await AppViewSet().init_app_async(self.app_id)
            await self.send(text_data=json.dumps({"session": {"id": self._session_id}}))

        if event == "stop":
            if self._output_stream is not None:
                self._output_stream.close()

    async def receive(self, text_data):
        loop = asyncio.get_running_loop()
        loop.create_task(
            self._respond_to_event(text_data),
        )


class ConnectionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self._activation_task = None

        if self.user.is_anonymous:
            await self.close()
            return

        self.connection_id = self.scope["url_route"]["kwargs"]["conn_id"]
        self.connection_activation_actor = ConnectionActivationActor.start(
            self.user,
            self.connection_id,
        ).proxy()
        await self.accept()

    async def disconnect(self, close_code):
        self.connection_activation_actor.stop()
        if self._activation_task and not self._activation_task.done():
            self._activation_task.cancel()
        self.close(code=close_code)

    async def _activate_connection(self):
        try:
            output = await self.connection_activation_actor.activate()
            async for c in output:
                if isinstance(c, Connection):
                    if c.status == ConnectionStatus.ACTIVE:
                        await self.connection_activation_actor.set_connection(c)
                    await self.send(
                        text_data=json.dumps(
                            {"event": "success" if c.status == ConnectionStatus.ACTIVE else "error"},
                        ),
                    )
                    self.connection_activation_actor.stop()
                elif isinstance(c, ConnectionActivationOutput):
                    await self.send(
                        text_data=json.dumps(
                            {"event": "output", "output": c.data},
                        ),
                    )
                elif isinstance(c, dict):
                    connection = c.get("connection", None)
                    if connection:
                        await self.connection_activation_actor.set_connection(connection)
                    if c.get("error", None):
                        await self.send(
                            text_data=json.dumps(
                                {"event": "error", "error": c.get("error")},
                            ),
                        )
                await asyncio.sleep(0.01)
        except Exception as e:
            logger.exception(e)
            self.connection_activation_actor.stop()

    async def _handle_input(self, text_data=None, bytes_data=None):
        try:
            await self.connection_activation_actor.input(ConnectionActivationInput(data=text_data)).get()
        except Exception as e:
            logger.exception(e)

    async def receive(self, text_data=None, bytes_data=None):
        json_data = json.loads(text_data or "{}")
        input = json_data.get("input", {})
        event = json_data.get("event", None)

        if event == "activate":
            loop = asyncio.get_running_loop()
            self._activation_task = loop.create_task(
                self._activate_connection(),
            )

        if event == "input" and input == "terminate":
            try:
                self.connection_activation_actor.input(
                    ConnectionActivationInput(data=input),
                )
            except Exception:
                pass
            finally:
                self.disconnect(1000)
