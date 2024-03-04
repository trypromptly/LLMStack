import hashlib
import hmac
import logging
from time import time

from pydantic import Field, SecretStr
from rest_framework.exceptions import PermissionDenied

from llmstack.apps.models import App
from llmstack.apps.types.app_type_interface import AppTypeInterface, BaseSchema

logger = logging.getLogger(__name__)


class SlackAppConfigSchema(BaseSchema):
    app_id: str = Field(
        title="App ID",
        description="App ID of the Slack app. Your application's ID can be found in the URL of the your application console.",
    )
    bot_token: str = Field(
        title="Bot Token",
        widget="password",
        description="Bot token to use for sending messages to Slack. Make sure the Bot has access to app_mentions:read and chat:write scopes. This token is available at Features > OAuth & Permissions in your app page. More details https://api.slack.com/authentication/oauth-v2",
    )
    verification_token: SecretStr = Field(
        title="Verification Token",
        widget="password",
        description="Verification token to verify the request from Slack. This token is available at Features > Basic Information in your app page. More details https://api.slack.com/authentication/verifying-requests-from-slack",
    )
    signing_secret: SecretStr = Field(
        title="Signing Secret",
        widget="password",
        description="Signing secret to verify the request from Slack. This secret is available at Features > Basic Information in your app page. More details https://api.slack.com/authentication/verifying-requests-from-slack",
    )
    slash_command_name: str = Field(
        default="promptly",
        title="Slash Command Name",
        description="The name of the slash command that will be used to trigger the app. Slack commands must start with a slash, be all lowercase, and contain no spaces. Examples: /deploy, /ack, /weather. Ensure that the bot has access to the commands scope under Features > OAuth & Permissions.",
        required=True,
    )
    slash_command_description: str = Field(
        title="Slash Command Description",
        default="Promptly App",
        description="The description of the slash command that will be used to trigger the app.",
        required=True,
    )


class SlackApp(AppTypeInterface[SlackAppConfigSchema]):
    @staticmethod
    def slug() -> str:
        return "slack"

    @staticmethod
    def name() -> str:
        return "Slack App"

    @staticmethod
    def description() -> str:
        return "Slack app that can be used to send messages to Slack"

    @classmethod
    def verify_request_signature(
        cls,
        app: App,
        headers: dict,
        raw_body: bytes,
    ):
        signature = headers.get("X-Slack-Signature")
        timestamp = headers.get("X-Slack-Request-Timestamp")
        if signature and timestamp and raw_body:
            signing_secret = app.slack_config.get("signing_secret", "")

            if signing_secret:
                if abs(time() - int(timestamp)) > 60 * 5:
                    raise PermissionDenied()

                format_req = str.encode(
                    f"v0:{timestamp}:{raw_body.decode('utf-8')}",
                )
                encoded_secret = str.encode(signing_secret)
                request_hash = hmac.new(
                    encoded_secret,
                    format_req,
                    hashlib.sha256,
                ).hexdigest()
                if f"v0={request_hash}" != signature:
                    logger.error(
                        f"Request signature verification failed for Slack app {app.id}",
                    )
                    raise PermissionDenied()
        return True
