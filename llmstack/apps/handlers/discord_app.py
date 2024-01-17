import logging
import uuid

from llmstack.apps.apis import AppRunnerException
from llmstack.apps.handlers.app_runnner import AppRunner
from llmstack.apps.integration_configs import DiscordIntegrationConfig
from llmstack.apps.models import AppVisibility
from llmstack.play.actor import ActorConfig
from llmstack.play.actors.bookkeeping import BookKeepingActor
from llmstack.play.actors.input import InputActor
from llmstack.play.actors.output import OutputActor
from llmstack.play.utils import convert_template_vars_from_legacy_format
from llmstack.processors.providers.discord.send_message import (
    DiscordSendMessageProcessor,
)

logger = logging.getLogger(__name__)


class InvalidDiscordRequestSignature(AppRunnerException):
    status_code = 401
    details = "Invalid Discord request signature"


def generate_uuid(input_str):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, input_str))


def process_discord_message_text(text):
    return text.strip()


class DiscordBotRunner(AppRunner):
    def app_init(self):
        self.discord_config = (
            DiscordIntegrationConfig().from_dict(
                self.app.discord_integration_config,
                self.app_owner_profile.decrypt_value,
            )
            if self.app.discord_integration_config
            else None
        )

        self.discord_bot_token = self.discord_config.get("bot_token")
        self.session_id = self._get_discord_bot_seession_id(self.request.data)

    def _get_discord_bot_seession_id(self, discord_request_payload):
        if "id" in discord_request_payload:
            return generate_uuid(discord_request_payload["id"])
        return None

    def _get_input_data(self):
        discord_request_payload = self.request.data
        discord_message_type = discord_request_payload["type"]
        if discord_message_type == 1:
            return {
                "input": {
                    "token": discord_request_payload["token"],
                    "type": 1,
                },
            }
        else:
            if (
                discord_message_type == 2
                and discord_request_payload["data"]["name"] == self.discord_config["slash_command_name"]
            ):
                app_input = {}

                for option in discord_request_payload["data"]["options"]:
                    app_input[option["name"]] = option["value"]

                return {
                    "input": {
                        "user": discord_request_payload["member"]["user"]["id"],
                        "username": discord_request_payload["member"]["user"]["username"],
                        "global_name": discord_request_payload["member"]["user"]["global_name"],
                        "channel": discord_request_payload["channel_id"],
                        "guild_id": discord_request_payload["guild_id"],
                        "token": discord_request_payload["token"],
                        **app_input,
                    },
                }

        raise Exception("Invalid Discord request")

    def _get_discord_processor_actor_configs(self, input_data):
        output_template = convert_template_vars_from_legacy_format(
            self.app_data["output_template"].get(
                "markdown",
                "",
            )
            if self.app_data and "output_template" in self.app_data
            else self.app.output_template.get(
                "markdown",
                "",
            ),
        )

        vendor_env = self.app_owner_profile.get_vendor_env()

        return ActorConfig(
            name="discord_processor",
            template_key="discord_processor",
            actor=DiscordSendMessageProcessor,
            kwargs={
                "env": vendor_env,
                "input": {
                    "discord_user_id": input_data["input"]["user"],
                    "discord_username": input_data["input"]["username"],
                    "discord_global_name": input_data["input"]["global_name"],
                    "token": input_data["input"]["token"],
                    "bot_token": self.discord_bot_token,
                    "channel_id": input_data["input"]["channel"],
                    "text": output_template,
                    "app_id": self.discord_config["app_id"],
                },
                "config": {},
                "session_data": {},
            },
            output_cls=DiscordSendMessageProcessor.get_output_cls(),
        )

    def _is_app_accessible(self):
        if self.app.visibility != AppVisibility.PUBLIC:
            raise Exception("Invalid app visibility for discord app")

        return super()._is_app_accessible()

    def _get_csp(self):
        return "frame-ancestors self"

    def _get_bookkeeping_actor_config(self, processor_configs):
        if self.app.type.slug == "agent":
            return ActorConfig(
                name="bookkeeping",
                template_key="bookkeeping",
                actor=BookKeepingActor,
                dependencies=[
                    "_inputs0",
                    "output",
                    "discord_processor",
                    "agent",
                ],
                kwargs={
                    "processor_configs": processor_configs,
                    "is_agent": True,
                },
            )
        else:
            return ActorConfig(
                name="bookkeeping",
                template_key="bookkeeping",
                actor=BookKeepingActor,
                dependencies=[
                    "_inputs0",
                    "output",
                    "discord_processor",
                ],
                kwargs={
                    "processor_configs": processor_configs,
                },
            )

    def _get_base_actor_configs(self, output_template, processor_configs):
        actor_configs = []
        if self.app.type.slug == "agent":
            pass
        else:
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
                        "template": "{{_inputs0.channel}}",
                    },
                ),
            ]
        return actor_configs

    def run_app(self):
        # Check if the app access permissions are valid
        self._is_app_accessible()

        csp = self._get_csp()

        processor_actor_configs, processor_configs = self._get_processor_actor_configs()

        template = convert_template_vars_from_legacy_format(
            self.app_data["output_template"].get(
                "markdown",
                "",
            )
            if self.app_data and "output_template" in self.app_data
            else self.app.output_template.get(
                "markdown",
                "",
            ),
        )

        # Actor configs
        actor_configs = self._get_base_actor_configs(
            template,
            processor_configs,
        )

        if self.app.type.slug == "agent":
            actor_configs.extend(
                map(
                    lambda x: ActorConfig(
                        name=x.name,
                        template_key=x.template_key,
                        actor=x.actor,
                        dependencies=(x.dependencies + ["agent"]),
                        kwargs=x.kwargs,
                    ),
                    processor_actor_configs,
                ),
            )
        else:
            actor_configs.extend(processor_actor_configs)

        # Add our discord processor responsible for sending the outgoing
        # message
        actor_configs.append(
            self._get_discord_processor_actor_configs(
                self._get_input_data(),
            ),
        )
        actor_configs.append(
            self._get_bookkeeping_actor_config(processor_configs),
        )

        if self.app.type.slug == "agent":
            self._start_agent(
                self._get_input_data(),
                self.app_session,
                actor_configs,
                csp,
                template,
                processor_configs,
            )
        else:
            self._start(
                self._get_input_data(),
                self.app_session,
                actor_configs,
                csp,
                template,
            )
        return {"type": 5}
