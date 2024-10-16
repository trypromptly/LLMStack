import asyncio
import logging
import uuid
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel

from llmstack.apps.runner.app_coordinator import AppCoordinator
from llmstack.common.blocks.base.schema import StrEnum
from llmstack.events.apis import EventsViewSet
from llmstack.play.actor import ActorConfig
from llmstack.processors.providers.processors import ProcessorFactory

logger = logging.getLogger(__name__)


class AppRunnerSourceType(str, Enum):
    PLAYGROUND = "playground"
    PLATFORM = "platform"
    APP_STORE = "app_store"
    SLACK = "slack"
    TWILIO = "twilio"
    DISCORD = "discord"
    WEB = "web"

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self)


class AppRunnerSource(BaseModel):
    type: AppRunnerSourceType
    id: str


class WebAppRunnerSource(AppRunnerSource):
    type: AppRunnerSourceType = AppRunnerSourceType.WEB
    request_ip: str
    request_location: str
    request_user_agent: str
    request_content_type: str


class PlatformAppRunnerSource(AppRunnerSource):
    type: AppRunnerSourceType = AppRunnerSourceType.PLATFORM


class AppStoreAppRunnerSource(AppRunnerSource):
    type: AppRunnerSourceType = AppRunnerSourceType.APP_STORE


class SlackAppRunnerSource(AppRunnerSource):
    type: AppRunnerSourceType = AppRunnerSourceType.SLACK


class TwilioAppRunnerSource(AppRunnerSource):
    type: AppRunnerSourceType = AppRunnerSourceType.TWILIO


class DiscordAppRunnerSource(AppRunnerSource):
    type: AppRunnerSourceType = AppRunnerSourceType.DISCORD


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
    def _get_actor_configs_from_processors(
        self, processors: List[Dict], session_id: str, is_agent: bool, vendor_env: Dict = {}
    ):
        actor_configs = []
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
                    },
                    dependencies=processor.get("dependencies", []),
                    output_template=processor.get("output_template", None) if is_agent else None,
                ),
            )
        return actor_configs

    def __init__(
        self, session_id: str = None, app_data: Dict = {}, source: AppRunnerSource = None, vendor_env: Dict = {}
    ):
        self._session_id = session_id or str(uuid.uuid4())
        self._app_data = app_data
        self._source = source
        self._is_agent = app_data.get("type_slug") == "agent"

        actor_configs = self._get_actor_configs_from_processors(
            app_data.get("processors", []), self._session_id, self._is_agent, vendor_env
        )
        output_template = app_data.get("output_template", {}).get("markdown", "")
        self._coordinator = AppCoordinator.start(actor_configs=actor_configs, output_template=output_template).proxy()

    async def stop(self):
        await self._coordinator.stop()

    async def run(self, request: AppRunnerRequest):
        # TODO: Add bookkeeping to history on output

        request_id = str(uuid.uuid4())

        # Build a Message with request.input and send it to the coordinator

        self._coordinator.input(request.input)

        yield AppRunnerStreamingResponse(
            id=request_id,
            client_request_id=request.client_request_id,
            type=AppRunnerStreamingResponseType.OUTPUT_STREAM_BEGIN,
        )
        async for output in await self._coordinator.output().get():
            if "chunks" in output:
                # Received all chunks
                break

            await asyncio.sleep(0.0001)
            yield AppRunnerStreamingResponse(
                id=request_id,
                client_request_id=request.client_request_id,
                type=AppRunnerStreamingResponseType.OUTPUT_STREAM_CHUNK,
                data=AppRunnerResponseOutputChunkData(deltas=output["deltas"], chunk=output["chunk"]),
            )

        yield AppRunnerStreamingResponse(
            id=request_id,
            client_request_id=request.client_request_id,
            type=AppRunnerStreamingResponseType.OUTPUT_STREAM_END,
        )

        # Send the final output
        if "chunks" in output:
            yield AppRunnerStreamingResponse(
                id=request_id,
                client_request_id=request.client_request_id,
                type=AppRunnerStreamingResponseType.OUTPUT,
                data=AppRunnerResponseOutputData(output=output["output"], chunks=output["chunks"]),
            )

            # Persist bookkeeping data
            bookkeeping_data = self._coordinator.bookkeeping_data().get().get()
            EventsViewSet().create(
                "app.run.finished",
                {
                    "bookkeeping_data_map": bookkeeping_data,
                },
            )
