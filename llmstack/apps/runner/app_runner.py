import asyncio
import logging
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from asgiref.sync import sync_to_async
from pydantic import BaseModel

from llmstack.apps.runner.app_coordinator import AppCoordinator
from llmstack.common.blocks.base.schema import StrEnum
from llmstack.events.apis import EventsViewSet
from llmstack.play.actor import ActorConfig
from llmstack.play.utils import extract_variables_from_liquid_template
from llmstack.processors.providers.processors import ProcessorFactory

logger = logging.getLogger(__name__)


def iter_over_async(ait, loop):
    ait = ait.__aiter__()

    async def get_next():
        try:
            obj = await ait.__anext__()
            return False, obj
        except StopAsyncIteration:
            return True, None

    while True:
        done, obj = loop.run_until_complete(get_next())
        if done:
            break
        yield obj


class AppRunnerSourceType(str, Enum):
    PLAYGROUND = "playground"
    PLATFORM = "platform"
    APP_STORE = "app_store"
    SLACK = "slack"
    TWILIO = "twilio"
    DISCORD = "discord"
    SHEET = "sheet"
    WEB = "web"
    API = "api"

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self)


class AppRunnerSource(BaseModel):
    type: AppRunnerSourceType
    request_user_email: Optional[str] = None
    request_user: Optional[Any] = None

    @property
    def id(self):
        raise NotImplementedError

    def effects(self, request_id, session_id, output, bookkeeping_data):
        """
        Source specific effects from the app run
        """
        EventsViewSet().create(
            "app.run.finished",
            {
                "output": output,
                "bookkeeping_data_map": bookkeeping_data,
                "request_data": {
                    **(self.model_dump()),
                    "id": self.id,
                    "request_id": request_id,
                    "session_id": session_id,
                },
                "usage_metrics": dict(
                    map(
                        lambda key: (key, bookkeeping_data[key].get("usage_data", {}).get("usage_metrics", [])),
                        bookkeeping_data.keys(),
                    )
                ),
            },
        )


class WebAppRunnerSource(AppRunnerSource):
    type: AppRunnerSourceType = AppRunnerSourceType.WEB
    request_ip: str
    request_location: str
    request_user_agent: str
    request_content_type: str
    app_uuid: str

    @property
    def id(self):
        return self.app_uuid


class APIAppRunnerSource(WebAppRunnerSource):
    type: AppRunnerSourceType = AppRunnerSourceType.API


class PlaygroundAppRunnerSource(AppRunnerSource):
    type: AppRunnerSourceType = AppRunnerSourceType.PLAYGROUND
    provider_slug: str
    processor_slug: str
    request_ip: Optional[str] = ""
    request_location: Optional[str] = ""
    request_user_agent: Optional[str] = ""

    @property
    def id(self):
        return f"{self.provider_slug}/{self.processor_slug}"


class PlatformAppRunnerSource(AppRunnerSource):
    type: AppRunnerSourceType = AppRunnerSourceType.PLATFORM
    slug: str

    @property
    def id(self):
        return self.slug


class StoreAppRunnerSource(AppRunnerSource):
    type: AppRunnerSourceType = AppRunnerSourceType.APP_STORE
    slug: str
    request_ip: Optional[str] = None
    request_location: Optional[str] = None
    request_user_agent: Optional[str] = None

    @property
    def id(self):
        return self.slug


class SlackAppRunnerSource(AppRunnerSource):
    type: AppRunnerSourceType = AppRunnerSourceType.SLACK
    app_uuid: str

    @property
    def id(self):
        return self.app_uuid


class TwilioSMSAppRunnerSource(AppRunnerSource):
    type: AppRunnerSourceType = AppRunnerSourceType.TWILIO
    app_uuid: str

    @property
    def id(self):
        return self.app_uuid


class DiscordAppRunnerSource(AppRunnerSource):
    type: AppRunnerSourceType = AppRunnerSourceType.DISCORD
    app_uuid: str

    @property
    def id(self):
        return self.app_uuid


class SheetProcessorRunnerSource(PlaygroundAppRunnerSource):
    type: AppRunnerSourceType = AppRunnerSourceType.SHEET
    sheet_id: str

    @property
    def id(self):
        return f"{self.provider_slug}/{self.processor_slug}"


class SheetStoreAppRunnerSource(StoreAppRunnerSource):
    type: AppRunnerSourceType = AppRunnerSourceType.SHEET
    request_ip: str = ""
    request_location: str = ""
    request_user_agent: str = "Promptly"
    sheet_id: str

    @property
    def id(self):
        return self.slug


class AppRunnerStreamingResponseType(StrEnum):
    ERRORS = "errors"
    OUTPUT = "output"
    OUTPUT_STREAM_CHUNK = "output_stream_chunk"
    OUTPUT_STREAM_BEGIN = "output_stream_begin"
    OUTPUT_STREAM_END = "output_stream_end"


class AppRunnerResponseError(BaseModel):
    code: Optional[int] = None
    message: str


class AppRunnerResponseData(BaseModel):
    pass


class AppRunnerResponseErrorsData(AppRunnerResponseData):
    errors: List[AppRunnerResponseError]


class AppRunnerResponseOutputData(AppRunnerResponseData):
    output: Dict[str, str]
    chunks: Optional[Dict] = None  # Stitched structured output from all the processors


class AppRunnerResponseOutputChunkData(AppRunnerResponseData):
    deltas: Optional[Dict[str, str]] = None  # delta to be applied to each actor's output
    chunk: Optional[Dict] = None  # Structured output from each processor


class AppRunnerRequest(BaseModel):
    client_request_id: Optional[str] = None  # ID sent by the client
    session_id: str
    input: Dict


class AppRunnerResponse(BaseModel):
    id: str  # ID of the request
    client_request_id: Optional[str] = None  # ID sent by the client
    output: Optional[str] = None
    chunks: Optional[Dict] = None  # Stitched structured output from all the processors
    errors: Optional[List[AppRunnerResponseError]] = None


class AppRunnerStreamingResponse(BaseModel):
    id: str  # ID of the request
    client_request_id: Optional[str] = None  # ID sent by the client
    type: AppRunnerStreamingResponseType
    data: Optional[
        Union[AppRunnerResponseErrorsData, AppRunnerResponseOutputChunkData, AppRunnerResponseOutputData]
    ] = None


class AppRunner:
    def _compute_dependencies_from_processor(self, processor: Dict, allowed_variables: List[str] = []):
        dependencies = []

        def process_dict(d):
            for value in d.values():
                if isinstance(value, str):
                    dependencies.extend(extract_variables_from_liquid_template(value))
                elif isinstance(value, dict):
                    process_dict(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            process_dict(item)
                        elif isinstance(item, str):
                            dependencies.extend(extract_variables_from_liquid_template(item))

        process_dict(processor.get("config", {}))
        process_dict(processor.get("input", {}))

        return list(set(dep[0] for dep in dependencies if dep[0] in allowed_variables))

    async def _preprocess_input_files(
        self, request_id, input_data, input_fields, session_id, app_uuid, user, upload_file_fn
    ):
        from llmstack.apps.models import AppSessionFiles
        from llmstack.assets.stream import AssetStream

        for field in input_fields:
            if field["name"] in input_data:
                if field["type"] == "file":
                    input_data[field["name"]] = await sync_to_async(upload_file_fn)(
                        input_data[field["name"]], session_id, app_uuid, user
                    )
                elif (
                    field["type"] == "multi" and "files" in input_data[field["name"]] and not field.get("stream", False)
                ):
                    # multi has a list of files to upload
                    files = input_data[field["name"]]["files"]
                    for file in files[:5]:
                        file["data"] = await sync_to_async(upload_file_fn)(file["data"], session_id, app_uuid, user)
                    input_data[field["name"]]["files"] = files
                elif field["type"] == "multi" and field.get("stream", False):
                    # For input streaming, we need to create streaming objrefs for input, audio and transcript
                    objref_prefix = f"{app_uuid}/{session_id}/{request_id}"
                    asset_metadata = {
                        "app_uuid": app_uuid,
                        "username": self._source.request_user_email,
                    }

                    input_data[field["name"]]["text"] = AssetStream(
                        await sync_to_async(AppSessionFiles.create_streaming_asset)(
                            metadata={
                                **asset_metadata,
                                "file_name": f"{objref_prefix}_text",
                                "mime_type": "text/plain",
                            },
                            ref_id=session_id,
                        )
                    )

                    input_data[field["name"]]["audio"] = AssetStream(
                        await sync_to_async(AppSessionFiles.create_streaming_asset)(
                            metadata={
                                **asset_metadata,
                                "file_name": f"{objref_prefix}_audio",
                                "mime_type": "audio/webm",
                            },
                            ref_id=session_id,
                        )
                    )

                    input_data[field["name"]]["transcript"] = AssetStream(
                        await sync_to_async(AppSessionFiles.create_streaming_asset)(
                            metadata={
                                **asset_metadata,
                                "file_name": f"{objref_prefix}_transcript",
                                "mime_type": "text/plain",
                            },
                            ref_id=session_id,
                        )
                    )

        return input_data

    def _get_actor_configs_from_processors(
        self, processors: List[Dict], session_id: str, is_agent: bool, vendor_env: Dict = {}
    ):
        actor_configs = []
        allowed_processor_variables = [p["id"] for p in processors] + ["_inputs0"]
        for processor in processors:
            if "processor_slug" not in processor or "provider_slug" not in processor:
                logger.warning(
                    "processor_slug and provider_slug are required for each processor",
                )
                continue

            processor_cls = ProcessorFactory.get_processor(
                processor["processor_slug"],
                processor["provider_slug"],
            )
            actor_configs.append(
                ActorConfig(
                    name=processor["id"],
                    actor=processor_cls,
                    kwargs={
                        "input": processor.get("input", {}),
                        "config": processor.get("config", {}),
                        "env": vendor_env,
                        "session_id": session_id,
                        "request_user": self._source.request_user,
                        "app_uuid": self._source.id,
                        "input_fields": processor.get("input_fields", []),
                        "is_tool": is_agent,
                        "output_template": processor.get("output_template", {"markdown": ""}) if is_agent else None,
                    },
                    dependencies=self._compute_dependencies_from_processor(processor, allowed_processor_variables),
                    tool_schema=(
                        {
                            "type": "function",
                            "function": {
                                "name": processor["id"],
                                "description": processor["description"],
                                "parameters": processor_cls.get_tool_input_schema(processor),
                            },
                        }
                        if is_agent
                        else None
                    ),
                ),
            )
        return actor_configs

    def _get_bookkeeping_data(self):
        """
        Return a dictionary of bookkeeping data from the queue
        """
        bookkeeping_data = {}
        while not self._bookkeeping_queue.empty():
            stream_id, data = self._bookkeeping_queue.get_nowait()
            bookkeeping_data[stream_id] = data
            self._bookkeeping_queue.task_done()

        return bookkeeping_data

    def __init__(
        self,
        session_id: str = None,
        app_data: Dict = {},
        source: AppRunnerSource = None,
        vendor_env: Dict = {},
        file_uploader: Optional[Callable] = None,
    ):
        self._session_id = session_id or str(uuid.uuid4())
        self._app_data = app_data
        self._app_config = app_data.get("config", {})
        self._realtime = self._app_config.get("realtime", False)
        self._source = source
        self._is_agent = app_data.get("type_slug") == "agent"
        self._file_uploader = file_uploader
        self._bookkeeping_queue = asyncio.Queue()

        actor_configs = self._get_actor_configs_from_processors(
            app_data.get("processors", []), self._session_id, self._is_agent, vendor_env
        )
        output_template = app_data.get("output_template", {}).get("markdown", "")

        self._coordinator = AppCoordinator.start(
            actor_configs=actor_configs,
            output_template=output_template,
            is_agent=self._is_agent,
            env=vendor_env,
            config=self._app_config,
            bookkeeping_queue=self._bookkeeping_queue,
            metadata={
                "app_uuid": self._source.id,
                "username": self._source.request_user_email,
                "session_id": self._session_id,
            },
            spread_output_for_keys=app_data.get("spread_output_for_keys", set()),
        ).proxy()

    async def stop(self):
        await self._coordinator.stop()

        # Check if there is any pending bookkeeping data
        bookkeeping_data = self._get_bookkeeping_data()
        if bookkeeping_data:
            self._source.effects(
                self._request_id, self._session_id, bookkeeping_data.get("output", {}), bookkeeping_data
            )

    async def run(self, request: AppRunnerRequest):
        self._request_id = str(uuid.uuid4())

        # Clear the bookkeeping queue
        while not self._bookkeeping_queue.empty():
            self._bookkeeping_queue.get_nowait()
            self._bookkeeping_queue.task_done()

        # Pre-process run input to convert files to objrefs
        input_data = request.input
        input_fields = self._app_data.get("input_fields", [])
        if input_data and self._file_uploader:
            input_data = await self._preprocess_input_files(
                self._request_id,
                input_data,
                input_fields,
                self._session_id,
                self._source.id,
                self._source.request_user_email,
                self._file_uploader,
            )

        if self._realtime:
            # Find the multi stream input and send it as a single message
            for field in input_fields:
                if field.get("type", None) == "multi" and field.get("stream", None) and field["name"] in input_data:
                    input_data = {**input_data[field["name"]]}
                    input_data["metadata"] = {
                        "username": self._source.request_user_email,
                        "app_uuid": self._source.id,
                        "session_id": self._session_id,
                    }
                    break

        self._coordinator.input(self._request_id, input_data)

        yield AppRunnerStreamingResponse(
            id=self._request_id,
            client_request_id=request.client_request_id,
            type=AppRunnerStreamingResponseType.OUTPUT_STREAM_BEGIN,
        )
        async for output in await self._coordinator.output().get():
            if "chunks" in output:
                # Received all chunks
                break

            await asyncio.sleep(0.0001)

            if "errors" in output:
                yield AppRunnerStreamingResponse(
                    id=self._request_id,
                    client_request_id=request.client_request_id,
                    type=AppRunnerStreamingResponseType.ERRORS,
                    data=AppRunnerResponseErrorsData(
                        errors=[AppRunnerResponseError(message=error) for error in output.get("errors", [])]
                    ),
                )
            else:
                yield AppRunnerStreamingResponse(
                    id=self._request_id,
                    client_request_id=request.client_request_id,
                    type=AppRunnerStreamingResponseType.OUTPUT_STREAM_CHUNK,
                    data=AppRunnerResponseOutputChunkData(
                        deltas=output.get("deltas", {}), chunk=output.get("chunk", {})
                    ),
                )

        yield AppRunnerStreamingResponse(
            id=self._request_id,
            client_request_id=request.client_request_id,
            type=AppRunnerStreamingResponseType.OUTPUT_STREAM_END,
        )

        # Send the final output
        if "chunks" in output:
            # Persist bookkeeping data
            bookkeeping_data = self._get_bookkeeping_data()
            self._source.effects(
                self._request_id, self._session_id, bookkeeping_data.get("output", {}), bookkeeping_data
            )

            # Send the final output
            yield AppRunnerStreamingResponse(
                id=self._request_id,
                client_request_id=request.client_request_id,
                type=AppRunnerStreamingResponseType.OUTPUT,
                data=AppRunnerResponseOutputData(output=output.get("output", {}), chunks=output.get("chunks", {})),
            )

    def run_until_complete(self, request: AppRunnerRequest, event_loop):
        for response in iter_over_async(self.run(request), event_loop):
            if isinstance(response.data, AppRunnerResponseErrorsData) or isinstance(
                response.data, AppRunnerResponseOutputData
            ):
                break
        return response
