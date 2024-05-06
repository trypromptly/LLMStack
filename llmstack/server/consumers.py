import asyncio
import importlib
import json
import logging
import uuid

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, QueryDict
from django_ratelimit.exceptions import Ratelimited
from flags.state import flag_enabled

from llmstack.assets.utils import get_asset_by_objref
from llmstack.connections.actors import ConnectionActivationActor
from llmstack.connections.models import (
    Connection,
    ConnectionActivationInput,
    ConnectionActivationOutput,
    ConnectionStatus,
)
from llmstack.play.utils import run_coro_in_new_loop

logger = logging.getLogger(__name__)

usage_limiter_module = importlib.import_module(settings.LIMITER_MODULE)
is_ratelimited_fn = getattr(usage_limiter_module, "is_ratelimited", None)
is_usage_limited_fn = getattr(usage_limiter_module, "is_usage_limited", None)


class UsageLimitReached(PermissionDenied):
    pass


class OutOfCredits(PermissionDenied):
    pass


@database_sync_to_async
def _usage_limit_exceeded(request, user):
    return flag_enabled(
        "HAS_EXCEEDED_MONTHLY_PROCESSOR_RUN_QUOTA",
        request=request,
        user=user,
    )


@database_sync_to_async
def _build_request_from_input(post_data, scope):
    session = dict(scope["session"])
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
        "REMOTE_ADDR": headers.get(b"x-forwarded-for", b"").decode("utf-8").split(",")[0].strip(),
        "_prid": session.get("_prid", ""),
    }
    http_request.session = session
    http_request.method = method
    http_request.GET = query_params
    http_request.query_params = query_params
    http_request.stream = json.dumps(post_data)
    http_request.user = user
    http_request.data = post_data

    return http_request


class AppConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.app_id = self.scope["url_route"]["kwargs"]["app_id"]
        self.preview = True if "preview" in self.scope["url_route"]["kwargs"] else False
        self._session_id = None
        self._coordinator_ref = None
        await self.accept()

    async def disconnect(self, close_code):
        # TODO: Close the stream
        pass

    async def _run_app(self, request_uuid, request, **kwargs):
        from llmstack.apps.apis import AppViewSet

        return await AppViewSet().run_app_internal_async(
            uid=self.app_id,
            session_id=self._session_id,
            request_uuid=request_uuid,
            request=request,
            preview=self.preview,
        )

    async def _respond_to_event(self, text_data):
        from llmstack.apps.apis import AppViewSet

        json_data = json.loads(text_data)
        input = json_data.get("input", {})
        id = json_data.get("id", None)
        event = json_data.get("event", None)
        request_uuid = str(uuid.uuid4())
        self._session_id = self._session_id or json_data.get(
            "session_id",
            None,
        )

        if event == "run":
            try:
                request = await _build_request_from_input({"input": input, "stream": True}, self.scope)
                if is_ratelimited_fn(request, self._respond_to_event):
                    raise Ratelimited("Rate limit reached.")

                output_stream, self._coordinator_ref = await self._run_app(request_uuid=request_uuid, request=request)
                # Generate a uuid for the response
                response_id = str(uuid.uuid4())

                async for output in output_stream:
                    if "errors" in output or "session" in output:
                        if "session" in output:
                            self._session_id = output["session"]["id"]
                        await self.send(text_data=json.dumps({**output, **{"reply_to": id}}))
                    else:
                        await self.send(
                            text_data=json.dumps(
                                {"output": output, "reply_to": id, "id": response_id, "request_id": request_uuid}
                            )
                        )

                await self.send(
                    text_data=json.dumps(
                        {"event": "done", "reply_to": id, "id": response_id, "request_id": request_uuid}
                    )
                )
            except Ratelimited:
                await self.send(
                    text_data=json.dumps({"event": "ratelimited", "reply_to": id, "request_id": request_uuid})
                )
            except UsageLimitReached:
                await self.send(
                    text_data=json.dumps({"event": "usagelimited", "reply_to": id, "request_id": request_uuid})
                )
            except Exception as e:
                logger.exception(e)
                await self.send(text_data=json.dumps({"errors": [str(e)], "reply_to": id, "request_id": request_uuid}))

        if event == "init":
            # Create a new session and return the session id
            self._session_id = await AppViewSet().init_app_async(self.app_id)
            await self.send(text_data=json.dumps({"session": {"id": self._session_id}, "request_id": request_uuid}))

        if event == "stop":
            if self._coordinator_ref:
                self._coordinator_ref.stop()

    async def receive(self, text_data):
        run_coro_in_new_loop(self._respond_to_event(text_data))


class AssetStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self._category = self.scope["url_route"]["kwargs"]["category"]
        self._uuid = self.scope["url_route"]["kwargs"]["uuid"]
        self._session = self.scope["session"]
        self._request_user = self.scope["user"]
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def _respond_to_event(self, bytes_data):
        from llmstack.assets.apis import AssetStream

        if bytes_data:
            # Using b"\n" as delimiter
            chunks = bytes_data.split(b"\n")
            event = chunks[0]

            if event == b"read":
                asset = await database_sync_to_async(get_asset_by_objref)(
                    f"objref://{self._category}/{self._uuid}", self._request_user, self._session
                )
                if not asset:
                    # Close the connection
                    await self.close(code=1008)
                    return

                asset_stream = AssetStream(asset)
                for chunk in asset_stream.get_stream():
                    await self.send(bytes_data=chunk)

                await self.close()

    async def receive(self, text_data=None, bytes_data=None):
        run_coro_in_new_loop(self._respond_to_event(bytes_data))


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


class PlaygroundConsumer(AppConsumer):
    async def connect(self):
        self.app_id = None
        self.preview = False
        self._session_id = None
        self._coordinator_ref = None
        await self.accept()

    async def _run_app(self, request_uuid, request, **kwargs):
        from llmstack.apps.apis import AppViewSet

        if is_usage_limited_fn(request, self._run_app):
            raise UsageLimitReached("Usage limit reached. Please login to continue.")

        if await _usage_limit_exceeded(request, request.user):
            raise OutOfCredits(
                "You have exceeded your usage credits. Please add credits to your account from settings to continue using the platform.",
            )

        return await AppViewSet().run_playground_internal_async(
            session_id=self._session_id,
            request_uuid=request_uuid,
            request=request,
            preview=self.preview,
        )
