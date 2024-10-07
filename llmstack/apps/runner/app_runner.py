import logging
import uuid
from enum import Enum
from typing import Dict, List

from pydantic import BaseModel

from llmstack.apps.runner.agent_coordinator import AgentCoordinator
from llmstack.apps.runner.workflow_coordinator import WorkflowCoordinator
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


class AppRunnerRequest(BaseModel):
    id: str
    session_id: str
    request: Dict


class AppRunner:
    def _get_actor_configs_from_processors(self, processors: List[Dict], is_agent: bool, vendor_env: Dict = {}):
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
            app_data.get("processors", []), self._is_agent, vendor_env
        )
        output_template = app_data.get("output_template", {}).get("markdown", "")
        self._coordinator = (
            AgentCoordinator.start(
                actor_configs=actor_configs,
                output_template=output_template,
            ).proxy()
            if self._is_agent
            else WorkflowCoordinator.start(actor_configs=actor_configs, output_template=output_template).proxy()
        )

    async def run(self, request: AppRunnerRequest):
        return self._coordinator.input(request.request)

    async def output(self):
        return self._coordinator.output().get()

    async def output_stream(self):
        return self._coordinator.output_stream().get()

    async def stop(self):
        await self._coordinator.stop()
