import asyncio
import importlib
import json
import logging
import uuid

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, QueryDict
from flags.state import flag_enabled

from llmstack.apps.runner.app_runner import (
    AppRunnerRequest,
    AppRunnerStreamingResponseType,
    PlaygroundAppRunnerSource,
    StoreAppRunnerSource,
    WebAppRunnerSource,
)
from llmstack.assets.utils import get_asset_by_objref
from llmstack.common.utils.utils import get_location
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
        from llmstack.apps.apis import AppViewSet

        self._app_uuid = self.scope["url_route"]["kwargs"]["app_uuid"]
        self._preview = True if "preview" in self.scope["url_route"]["kwargs"] else False
        self._session_id = str(uuid.uuid4())
        self._user = self.scope.get("user", None)

        headers = dict(self.scope["headers"])
        request_ip = headers.get(
            "X-Forwarded-For",
            self.scope.get("client", [""])[0] or "",
        ).split(",")[
            0
        ].strip() or headers.get("X-Real-IP", "")
        request_location = headers.get("X-Client-Geo-Location", "")
        if not request_location:
            location = get_location(request_ip)
            request_location = f"{location.get('city', '')}, {location.get('country_code', '')}" if location else ""

        request_user_email = self.scope.get("user", None).email if self.scope.get("user", None) else None

        self._source = WebAppRunnerSource(
            id=self._session_id,
            request_ip=request_ip,
            request_location=request_location,
            request_user_agent=headers.get("User-Agent", ""),
            request_content_type=headers.get("Content-Type", ""),
            app_uuid=self._app_uuid,
            request_user_email=request_user_email,
        )
        self._app_runner = await AppViewSet().get_app_runner_async(
            self._session_id,
            self._app_uuid,
            self._source,
            self.scope.get("user", None),
            self._preview,
        )
        await self.accept()

    async def disconnect(self, close_code):
        if self._app_runner:
            await self._app_runner.stop()

    async def _respond_to_event(self, text_data):
        json_data = json.loads(text_data)
        client_request_id = json_data.get("id", None)
        event = json_data.get("event", None)

        if event == "run":
            app_runner_request = AppRunnerRequest(
                client_request_id=client_request_id,
                session_id=self._session_id,
                input=json_data.get("input", {}),
            )
            try:
                response_iterator = self._app_runner.run(app_runner_request)
                async for response in response_iterator:
                    if response.type == AppRunnerStreamingResponseType.OUTPUT_STREAM_CHUNK:
                        await self.send(text_data=json.dumps(response.model_dump()))
                    elif response.type == AppRunnerStreamingResponseType.ERRORS:
                        await self.send(
                            text_data=json.dumps(
                                {
                                    "errors": [error.message for error in response.data.errors],
                                    "request_id": client_request_id,
                                }
                            )
                        )
                    elif response.type == AppRunnerStreamingResponseType.OUTPUT_STREAM_END:
                        await self.send(text_data=json.dumps({"event": "done", "request_id": client_request_id}))
            except Exception as e:
                logger.exception(f"Failed to run app: {e}")
        elif event == "create_asset":
            from llmstack.apps.models import AppSessionFiles

            try:
                asset_data = json_data.get("data", {})
                asset_metadata = {
                    "file_name": asset_data.get("file_name", str(uuid.uuid4())),
                    "mime_type": asset_data.get("mime_type", "application/octet-stream"),
                    "app_uuid": self.app_id,
                    "username": (
                        self._user.username
                        if self._user and not self._user.is_anonymous
                        else self._session.get("_prid", "")
                    ),
                }

                asset = await sync_to_async(AppSessionFiles.create_asset)(
                    asset_metadata, self._session_id, streaming=asset_data.get("streaming", False)
                )

                if not asset:
                    await self.send(
                        text_data=json.dumps(
                            {
                                "errors": ["Failed to create asset"],
                                "reply_to": client_request_id,
                                "request_id": client_request_id,
                                "asset_request_id": client_request_id,
                            }
                        )
                    )
                    return

                output = {
                    "asset": asset.objref,
                    "reply_to": client_request_id,
                    "request_id": client_request_id,
                    "asset_request_id": client_request_id,
                }

                await self.send(text_data=json.dumps(output))
            except Exception as e:
                logger.exception(e)
                await self.send(
                    text_data=json.dumps(
                        {
                            "errors": [str(e)],
                            "reply_to": client_request_id,
                            "request_id": client_request_id,
                            "asset_request_id": client_request_id,
                        }
                    )
                )

        if event == "delete_asset":
            # Delete an asset in the session
            if not self._session_id:
                return

            # TODO: Implement delete asset
        elif event == "stop":
            self.disconnect()

    async def _respond_to_event_old(self, text_data):
        from llmstack.apps.apis import AppViewSet
        from llmstack.apps.models import AppSessionFiles

        json_data = json.loads(text_data)
        id = json_data.get("id", None)
        event = json_data.get("event", None)
        request_uuid = str(uuid.uuid4())
        self._session_id = self._session_id or json_data.get(
            "session_id",
            None,
        )
        self._user = self.scope.get("user", None)
        self._session = self.scope.get("session", None)

        # if event == "run":
        #     try:
        #         request = await _build_request_from_input({"input": input, "stream": True}, self.scope)
        #         if is_ratelimited_fn(request, self._respond_to_event):
        #             raise Ratelimited("Rate limit reached.")

        #         output_stream, self._coordinator_ref = await self._run_app(request_uuid=request_uuid, request=request)
        #         # Generate a uuid for the response
        #         response_id = str(uuid.uuid4())

        #         async for output in output_stream:
        #             if "errors" in output or "session" in output:
        #                 if "session" in output:
        #                     self._session_id = output["session"]["id"]
        #                 await self.send(text_data=json.dumps({**output, **{"reply_to": id}}))
        #             else:
        #                 await self.send(
        #                     text_data=json.dumps(
        #                         {"output": output, "reply_to": id, "id": response_id, "request_id": request_uuid}
        #                     )
        #                 )

        #         await self.send(
        #             text_data=json.dumps(
        #                 {"event": "done", "reply_to": id, "id": response_id, "request_id": request_uuid}
        #             )
        #         )
        #     except Ratelimited:
        #         await self.send(
        #             text_data=json.dumps({"event": "ratelimited", "reply_to": id, "request_id": request_uuid})
        #         )
        #     except UsageLimitReached:
        #         await self.send(
        #             text_data=json.dumps({"event": "usagelimited", "reply_to": id, "request_id": request_uuid})
        #         )
        #     except Exception as e:
        #         logger.exception(e)
        #         await self.send(text_data=json.dumps({"errors": [str(e)], "reply_to": id, "request_id": request_uuid}))

        if event == "init":
            # Create a new session and return the session id
            self._session_id = await AppViewSet().init_app_async(self.app_id)
            await self.send(text_data=json.dumps({"session": {"id": self._session_id}, "request_id": request_uuid}))

        if event == "create_asset":
            try:
                # Create an asset in the session. Returns asset info for the other side to upload content to
                session_created = False
                if not self._session_id:
                    self._session_id = await AppViewSet().init_app_async(self.app_id)
                    session_created = True

                asset_data = json_data.get("data", {})
                asset_metadata = {
                    "file_name": asset_data.get("file_name", str(uuid.uuid4())),
                    "mime_type": asset_data.get("mime_type", "application/octet-stream"),
                    "app_uuid": self.app_id,
                    "username": (
                        self._user.username
                        if self._user and not self._user.is_anonymous
                        else self._session.get("_prid", "")
                    ),
                }

                asset = await sync_to_async(AppSessionFiles.create_asset)(
                    asset_metadata, self._session_id, streaming=asset_data.get("streaming", False)
                )

                if not asset:
                    await self.send(
                        text_data=json.dumps(
                            {
                                "errors": ["Failed to create asset"],
                                "reply_to": id,
                                "request_id": request_uuid,
                                "asset_request_id": id,
                            }
                        )
                    )
                    return

                output = {
                    "asset": asset.objref,
                    "reply_to": id,
                    "request_id": request_uuid,
                    "asset_request_id": id,
                }

                if session_created:
                    output["session"] = {"id": self._session_id}

                await self.send(text_data=json.dumps(output))
            except Exception as e:
                logger.exception(e)
                await self.send(
                    text_data=json.dumps(
                        {"errors": [str(e)], "reply_to": id, "request_id": request_uuid, "asset_request_id": id}
                    )
                )

        if event == "delete_asset":
            # Delete an asset in the session
            if not self._session_id:
                return

            # TODO: Implement delete asset

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
        from llmstack.assets.stream import AssetStream

        if bytes_data:
            # Using b"\n" as delimiter
            chunks = bytes_data.split(b"\n")
            event = chunks[0]
            asset = await database_sync_to_async(get_asset_by_objref)(
                f"objref://{self._category}/{self._uuid}", self._request_user, self._session
            )
            if not asset:
                # Close the connection
                await self.close(code=1008)
                return

            asset_stream = AssetStream(asset)

            try:
                if event == b"read":
                    for chunk in asset_stream.read(start_index=0, timeout=10000):
                        await self.send(bytes_data=chunk)

                if event == b"write":
                    if bytes_data == b"write\n":
                        await sync_to_async(asset_stream.finalize)()
                        await self.close()
                        return

                    await sync_to_async(asset_stream.append_chunk)(bytes_data[6:])

            except Exception as e:
                logger.exception(e)
                await self.send(bytes_data=b"")
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
            except Exception as e:
                logger.exception(e)
                pass
            finally:
                self.disconnect(1000)


class PlaygroundConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        headers = dict(self.scope["headers"])
        request_ip = headers.get("X-Forwarded-For", self.scope.get("client", [""])[0] or "").split(",")[
            0
        ].strip() or headers.get("X-Real-IP", "")
        request_location = headers.get("X-Client-Geo-Location", "")
        if not request_location:
            location = get_location(request_ip)
            request_location = f"{location.get('city', '')}, {location.get('country_code', '')}" if location else ""

        request_user_email = self.scope.get("user", None).email if self.scope.get("user", None) else None

        self._source = PlaygroundAppRunnerSource(
            request_ip=request_ip,
            request_location=request_location,
            request_user_agent=headers.get("User-Agent", ""),
            request_content_type=headers.get("Content-Type", ""),
            request_user_email=request_user_email,
            processor_slug="",
            provider_slug="",
        )
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def _respond_to_event(self, text_data):
        from llmstack.apps.apis import PlaygroundViewSet

        json_data = json.loads(text_data)
        event_input = json_data.get("input", {})

        processor_slug = event_input.get("api_backend_slug")
        provider_slug = event_input.get("api_provider_slug")
        input_data = event_input.get("input", {})
        config_data = event_input.get("config", {})

        session_id = str(uuid.uuid4())
        source = self._source.model_copy(
            update={
                "session_id": session_id,
                "processor_slug": processor_slug,
                "provider_slug": provider_slug,
            }
        )

        client_request_id = json_data.get("id", None)
        app_runner_request = AppRunnerRequest(
            client_request_id=client_request_id, session_id=session_id, input=input_data
        )

        app_runner = await PlaygroundViewSet().get_app_runner_async(
            session_id, source, self.scope.get("user", None), input_data, config_data
        )
        try:
            response_iterator = app_runner.run(app_runner_request)
            async for response in response_iterator:
                if response.type == AppRunnerStreamingResponseType.OUTPUT_STREAM_CHUNK:
                    await self.send(text_data=json.dumps(response.model_dump()))
                elif response.type == AppRunnerStreamingResponseType.OUTPUT:
                    await self.send(
                        text_data=json.dumps(
                            {"event": "done", "request_id": client_request_id, "data": response.data.chunks}
                        )
                    )
        except Exception as e:
            logger.exception(f"Failed to run app: {e}")
        await app_runner.stop()

    async def receive(self, text_data):
        run_coro_in_new_loop(self._respond_to_event(text_data))


class StoreAppConsumer(AppConsumer):
    async def connect(self):
        from llmstack.app_store.apis import AppStoreAppViewSet

        self._app_slug = self.scope["url_route"]["kwargs"]["app_id"]
        self._session_id = str(uuid.uuid4())

        headers = dict(self.scope["headers"])
        request_ip = headers.get("X-Forwarded-For", self.scope.get("client", [""])[0] or "").split(",")[
            0
        ].strip() or headers.get("X-Real-IP", "")
        request_location = headers.get("X-Client-Geo-Location", "")
        if not request_location:
            location = get_location(request_ip)
            request_location = f"{location.get('city', '')}, {location.get('country_code', '')}" if location else ""

        request_user_email = self.scope.get("user", None).email if self.scope.get("user", None) else None

        self._source = StoreAppRunnerSource(
            slug=self._app_slug,
            request_ip=request_ip,
            request_location=request_location,
            request_user_agent=headers.get("User-Agent", ""),
            request_user_email=request_user_email,
        )

        self._app_runner = await AppStoreAppViewSet().get_app_runner_async(
            self._session_id, self._app_slug, self._source, self.scope.get("user", None)
        )
        await self.accept()
