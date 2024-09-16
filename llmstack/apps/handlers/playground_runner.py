import logging
import uuid
from collections import namedtuple

from llmstack.apps.app_session_utils import create_app_session_data
from llmstack.apps.handlers.app_runnner import AppRunner
from llmstack.connections.apis import ConnectionsViewSet
from llmstack.play.actor import ActorConfig
from llmstack.play.actors.bookkeeping import BookKeepingActor
from llmstack.play.actors.input import InputActor
from llmstack.play.actors.output import OutputActor
from llmstack.processors.providers.api_processors import ApiProcessorFactory

logger = logging.getLogger(__name__)

PlaygroundApp = namedtuple(
    "PlaygroundApp",
    ["id", "uuid", "type", "web_integration_config", "is_published"],
)
PlaygroundAppType = namedtuple("PlaygroundAppType", ["slug"])


def get_connections(profile):
    from django.test import RequestFactory

    request = RequestFactory().get("/api/connections/")
    request.user = profile.user
    response = ConnectionsViewSet().list(request)
    return dict(map(lambda entry: (entry["id"], entry), response.data))


class PlaygroundRunner(AppRunner):
    def _is_app_accessible(self):
        return True

    def app_init(self):
        self.session_id = str(uuid.uuid4())
        self.app_session = self._get_or_create_app_session()

    def _get_base_actor_configs(self, output_template, processor_configs):
        actor_configs = [
            ActorConfig(
                name="input",
                template_key="input",
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
                    "template": "{{ processor }}",
                },
            ),
        ]

        return actor_configs

    def _get_processor_actor_configs(self, processor_id):
        app_processor = None
        processor_actor_configs = []
        processor_configs = {}
        vendor_env = self.app_owner_profile.get_vendor_env()
        connections = get_connections(self.app_owner_profile)  # noqa

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
                dependencies=["input"],
                kwargs={
                    "id": app_processor["id"],
                    "env": vendor_env,
                    "input": app_processor["input"],
                    "config": app_processor["config"],
                    "metadata": {
                        "session_id": self.session_id,
                        "username": (
                            self.request.user.username
                            if self.request.user.is_authenticated
                            else self.request.session["_prid"]
                            if "_prid" in self.request.session
                            else ""
                        ),
                    },
                    "session_data": {},
                    "request": self.request,
                    "is_tool": False,
                    "session_enabled": False,
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

    def _get_bookkeeping_actor_config(self, processor_configs):
        return ActorConfig(
            name="bookkeeping",
            template_key="bookkeeping",
            actor=BookKeepingActor,
            dependencies=["input", "processor", "output"],
            kwargs={"processor_configs": processor_configs},
        )

    def run_app(self, processor_id):
        # Check if the app access permissions are valid
        self._is_app_accessible()

        csp = self._get_csp()

        processor_actor_configs, processor_configs = self._get_processor_actor_configs(
            processor_id,
        )
        actor_configs = self._get_actor_configs(
            self.app_data["output_template"].markdown,
            processor_configs,
            processor_actor_configs,
        )

        return self._start(
            self._get_input_data(),
            self.app_session,
            actor_configs,
            csp,
            self.app_data["output_template"].markdown,
        )
