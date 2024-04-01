import logging

from llmstack.apps.app_session_utils import (
    create_app_session_data,
    get_app_session_data,
)
from llmstack.apps.handlers.app_runnner import AppRunner
from llmstack.play.actor import ActorConfig
from llmstack.play.actors.input import InputActor
from llmstack.play.actors.output import OutputActor
from llmstack.processors.providers.api_processors import ApiProcessorFactory

logger = logging.getLogger(__name__)


class AppProcessorRunner(AppRunner):
    def _get_base_actor_configs(self, output_template, processor_configs):
        actor_configs = [
            ActorConfig(
                name="input",
                template_key="_inputs0",
                actor=InputActor,
                kwargs={
                    "input_request": self.input_actor_request,
                },
            ),
            ActorConfig(
                name="output",
                template_key="output",
                actor=OutputActor,
                kwargs={
                    "template": "{{ processor | tojson }}",
                },
            ),
        ]

        return actor_configs

    def _get_processor_actor_configs(self, processor_id):
        app_processor = None
        processor_actor_configs = []
        processor_configs = {}
        vendor_env = self.app_owner_profile.get_vendor_env()

        for processor in self.app_data["processors"]:
            if processor["id"] == processor_id:
                app_processor = processor
                break

        if "processor_slug" not in app_processor or "provider_slug" not in app_processor:
            raise Exception(
                "processor_slug and provider_slug are required for each processor",
            )

        processor_cls = ApiProcessorFactory.get_api_processor(
            app_processor["processor_slug"],
            app_processor["provider_slug"],
        )
        app_session_data = get_app_session_data(
            self.app_session,
            app_processor,
        )
        if not app_session_data:
            app_session_data = create_app_session_data(
                self.app_session,
                app_processor,
                {},
            )

        processor_actor_configs.append(
            ActorConfig(
                name=app_processor["id"],
                template_key="processor",
                actor=processor_cls,
                kwargs={
                    "id": app_processor["id"],
                    "env": vendor_env,
                    "input": {**app_processor["input"], **self.request.data.get("input", {})},
                    "config": app_processor["config"],
                    "session_data": app_session_data["data"] if app_session_data and "data" in app_session_data else {},
                    "request": self.request,
                    "is_tool": True if self.app.type.slug == "agent" else False,
                },
                output_cls=processor_cls.get_output_cls(),
            ),
        )
        processor_configs[processor["id"]] = {
            "app_session": self.app_session,
            "app_session_data": app_session_data,
            "processor": app_processor,
            "template_key": "processor",
        }

        return processor_actor_configs, processor_configs

    def run_app(self, processor_id):
        # Check if the app access permissions are valid
        self._is_app_accessible()

        csp = self._get_csp()

        template = ""
        processor_actor_configs, processor_configs = self._get_processor_actor_configs(
            processor_id,
        )
        actor_configs = self._get_actor_configs(
            template,
            processor_configs,
            processor_actor_configs,
        )

        if self.app.type.slug == "agent":
            return self._start_agent(
                self._get_input_data(),
                self.app_session,
                actor_configs,
                csp,
                template,
                processor_configs,
            )
        else:
            return self._start(
                self._get_input_data(),
                self.app_session,
                actor_configs,
                csp,
                template,
            )
