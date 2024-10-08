import logging
import re
import uuid

import requests
from django.contrib.auth.models import AnonymousUser, User

from llmstack.apps.app_session_utils import (
    create_agent_app_session_data,
    get_agent_app_session_data,
)
from llmstack.apps.handlers.app_runnner import AppRunner
from llmstack.apps.integration_configs import SlackIntegrationConfig
from llmstack.play.actor import ActorConfig
from llmstack.play.actors.agent import AgentActor
from llmstack.play.actors.bookkeeping import BookKeepingActor
from llmstack.play.actors.input import InputActor
from llmstack.play.actors.output import OutputActor
from llmstack.play.utils import convert_template_vars_from_legacy_format
from llmstack.processors.providers.slack.post_message import SlackPostMessageProcessor

logger = logging.getLogger(__name__)


def generate_uuid(input_str):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, input_str))


def process_slack_message_text(text):
    return re.sub(r"<@.*>(\|)?", "", text).strip()


def get_slack_user(slack_user_id, slack_bot_token):
    http_request = requests.get(
        "https://slack.com/api/users.info",
        params={
            "user": slack_user_id,
        },
        headers={
            "Authorization": f"Bearer {slack_bot_token}",
        },
    )

    slack_user = None
    if http_request.status_code == 200:
        http_response = http_request.json()
        slack_user = http_response["user"]["profile"]
    return slack_user


class SlackAppRunner(AppRunner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._slack_user = {}
        self._slack_user_email = ""

    def app_init(self):
        self.slack_config = (
            SlackIntegrationConfig().from_dict(
                self.app.slack_integration_config,
                self.app_owner_profile.decrypt_value,
            )
            if self.app.slack_integration_config
            else None
        )

        self.slack_bot_token = self.slack_config.get("bot_token")
        self.stream = False
        self.app_run_request_user = self._get_app_request_user(
            self.request.data,
        )
        self.session_id = self._get_slack_app_session_id(self.request.data)
        self.app_session = self._get_or_create_app_session()

    def _get_app_request_user(self, slack_request_payload):
        request_user = AnonymousUser()

        if "event" in slack_request_payload and "user" in slack_request_payload["event"]:
            slack_user_id = slack_request_payload["event"]["user"]
            try:
                self._slack_user = (
                    get_slack_user(
                        slack_user_id,
                        self.slack_bot_token,
                    )
                    or {}
                )
                # The email address of a Slack user is not guaranteed to be available for bot users.
                self._slack_user_email = self._slack_user.get("email") or ""
                user_object = (
                    User.objects.filter(email=self._slack_user_email).first() if self._slack_user_email else None
                )
                if user_object:
                    request_user = user_object
            except Exception as e:
                logger.exception(
                    f"Error in fetching user object from slack payload {slack_request_payload}: {e}",
                )

        return request_user

    def _get_slack_app_session_id(self, slack_request_payload):
        if slack_request_payload.get("type") == "event_callback" and "event" in slack_request_payload:
            thread_ts = None
            session_identifier = None
            if "thread_ts" in slack_request_payload["event"]:
                thread_ts = slack_request_payload["event"]["thread_ts"]
            elif "ts" in slack_request_payload["event"]:
                thread_ts = slack_request_payload["event"]["ts"]

            if "channel" in slack_request_payload["event"]:
                session_identifier = f"{slack_request_payload['event']['channel']}_{thread_ts}"
            else:
                session_identifier = f"{slack_request_payload['event']['user']}_{thread_ts}"

            id = f"{str(self.app.uuid)}-{session_identifier}"
            return generate_uuid(id)

        return None

    def _get_input_data(self):
        slack_request_payload = self.request.data

        slack_message_type = slack_request_payload["type"]
        if slack_message_type == "url_verification":
            return {"input": {"challenge": slack_request_payload["challenge"]}}
        elif slack_message_type == "event_callback":
            payload = process_slack_message_text(
                slack_request_payload["event"]["text"],
            )
            return {
                "input": {
                    "text": slack_request_payload["event"]["text"],
                    "user": slack_request_payload["event"]["user"],
                    "slack_user_email": self._slack_user_email,
                    "token": slack_request_payload["token"],
                    "team_id": slack_request_payload["team_id"],
                    "api_app_id": slack_request_payload["api_app_id"],
                    "team": slack_request_payload["event"]["team"],
                    "channel": slack_request_payload["event"]["channel"],
                    "text-type": slack_request_payload["event"]["type"],
                    "ts": slack_request_payload["event"]["ts"],
                    **dict(
                        zip(
                            list(map(lambda x: x["name"], self.app_data["input_fields"])),
                            [payload] * len(self.app_data["input_fields"]),
                        ),
                    ),
                },
            }
        else:
            raise Exception("Invalid Slack message type")

    def _get_slack_processor_actor_configs(self, input_data):
        output_template = convert_template_vars_from_legacy_format(
            (
                self.app_data["output_template"].get(
                    "markdown",
                    "",
                )
                if self.app_data and "output_template" in self.app_data
                else self.app.output_template.get(
                    "markdown",
                    "",
                )
            ),
        )
        vendor_env = self.app_owner_profile.get_vendor_env()
        if self.connections:
            vendor_env["connections"] = self.connections

        return ActorConfig(
            name="slack_processor",
            template_key="slack_processor",
            actor=SlackPostMessageProcessor,
            kwargs={
                "env": vendor_env,
                "input": {
                    "slack_user": input_data["input"]["user"],
                    "slack_user_email": input_data["input"]["slack_user_email"],
                    "token": self.slack_bot_token,
                    "channel": input_data["input"]["channel"],
                    "response_type": "text",
                    "text": output_template,
                    "thread_ts": input_data["input"]["ts"],
                },
                "config": {},
                "session_data": {},
            },
            output_cls=SlackPostMessageProcessor.get_output_cls(),
        )

    def _is_app_accessible(self):
        if (
            self.request.headers.get(
                "X-Slack-Request-Timestamp",
            )
            is None
            or self.request.headers.get("X-Slack-Signature") is None
        ):
            raise Exception("Invalid Slack request")

        request_type = self.request.data.get("type")

        # the request type should be either url_verification or event_callback
        is_valid_request_type = request_type in ["url_verification", "event_callback"]
        is_valid_app_token = self.request.data.get("token") == self.slack_config.get("verification_token")
        is_valid_app_id = self.request.data.get("api_app_id") == self.slack_config.get("app_id")

        # Validate that the app token, app ID and the request type are all valid.
        if not (is_valid_app_token and is_valid_app_id and is_valid_request_type):
            raise Exception("Invalid Slack request")

        # URL verification is allowed without any further checks
        if request_type == "url_verification":
            return True

        # Verify the request is coming from the app we expect and the event
        # type is app_mention
        elif request_type == "event_callback":
            event_data = self.request.data.get("event") or {}
            event_type = event_data.get("type")
            channel_type = event_data.get("channel_type")

            if event_type == "app_mention":
                return True

            elif event_type == "message":
                # Only allow direct messages from users and not from bots
                if channel_type == "im" and "subtype" not in event_data and "bot_id" not in event_data:
                    return True
            raise Exception(f"Invalid Slack request type: {event_type}, channel_type: {channel_type}")

        return super()._is_app_accessible()

    def _get_csp(self):
        return "frame-ancestors self"

    def _get_base_actor_configs(self, output_template, processor_configs):
        actor_configs = []
        if self.app.type.slug == "agent":
            input_data = self._get_input_data()
            agent_app_session_data = get_agent_app_session_data(
                self.app_session,
            )
            if not agent_app_session_data:
                agent_app_session_data = create_agent_app_session_data(
                    self.app_session,
                    {},
                )
            vendor_env = self.app_owner_profile.get_vendor_env()
            if self.connections:
                vendor_env["connections"] = self.connections
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
                    name="agent",
                    template_key="agent",
                    actor=AgentActor,
                    kwargs={
                        "processor_configs": processor_configs,
                        "functions": self._get_processors_as_functions(),
                        "input": input_data.get(
                            "input",
                            {},
                        ),
                        "env": vendor_env,
                        "config": self.app_data["config"],
                        "agent_app_session_data": agent_app_session_data,
                    },
                ),
                ActorConfig(
                    name="output",
                    template_key="output",
                    actor=OutputActor,
                    dependencies=["input"],
                    kwargs={
                        "template": "{{_inputs0.user}}",
                    },
                ),
            ]
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
                    dependencies=["input"],
                    kwargs={
                        "template": "{{_inputs0.user}}",
                    },
                ),
            ]
        return actor_configs

    def _get_bookkeeping_actor_config(self, processor_configs):
        if self.app.type.slug == "agent":
            return ActorConfig(
                name="bookkeeping",
                template_key="bookkeeping",
                actor=BookKeepingActor,
                dependencies=[
                    "_inputs0",
                    "output",
                    "slack_processor",
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
                    "slack_processor",
                ],
                kwargs={
                    "processor_configs": processor_configs,
                },
            )

    def _get_actor_configs(
        self,
        template,
        processor_configs,
        processor_actor_configs,
    ):
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

        # Add our slack processor responsible to sending the outgoing message
        actor_configs.append(
            self._get_slack_processor_actor_configs(
                self._get_input_data(),
            ),
        )
        actor_configs.append(
            self._get_bookkeeping_actor_config(processor_configs),
        )
        return actor_configs
