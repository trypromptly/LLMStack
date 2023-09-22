import logging
import time
from typing import Any
from typing import List
from typing import Optional

from asgiref.sync import async_to_sync

from llmstack.common.blocks.http import BearerTokenAuth, HttpAPIProcessor, HttpAPIProcessorInput, HttpMethod, JsonBody
from llmstack.play.actor import BookKeepingData
from processors.providers.api_processor_interface import ApiProcessorInterface
from processors.providers.api_processor_interface import ApiProcessorSchema


logger = logging.getLogger(__name__)


class DiscordEmbed(ApiProcessorSchema):
    title: str
    description: str
    color: Optional[int]


class DiscordSendMessageInput(ApiProcessorSchema):
    discord_user_id: str
    discord_username: str
    discord_global_name: str
    app_id: str
    token: str
    bot_token: str
    channel_id: str
    text: str
    embeds: Optional[List[DiscordEmbed]]


class DiscordSendMessageOutput(ApiProcessorSchema):
    code: int


class DiscordSendMessageConfiguration(ApiProcessorSchema):
    pass


class DiscordSendMessageProcessor(
    ApiProcessorInterface[
        DiscordSendMessageInput, DiscordSendMessageOutput, DiscordSendMessageConfiguration,
    ],
):
    """
    Discord Send Message API
    """

    @staticmethod
    def name() -> str:
        return 'discord/send_message'

    @staticmethod
    def slug() -> str:
        return 'send_message'

    @staticmethod
    def provider_slug() -> str:
        return 'discord'

    def _send_message(self, app_id: str, message: str, token: str) -> None:
        url = f"https://discord.com/api/v10/webhooks/{app_id}/{token}"
        http_processor = HttpAPIProcessor(configuration={'timeout': 60})
        response = http_processor.process(
            HttpAPIProcessorInput(
                url=url,
                method=HttpMethod.POST,
                headers={'Content-Type': 'application/json'},
                authorization=BearerTokenAuth(token=token),
                body=JsonBody(
                    json_body={
                        'content': message,
                    },
                ),
            ).dict(),
        )
        return response

    def process(self) -> dict:
        _env = self._env
        input = self._input.dict()
        response = self._send_message(
            input['app_id'], input['text'], input['token'])

        async_to_sync(self._output_stream.write)(
            DiscordSendMessageOutput(code=200),
        )

        return self._output_stream.finalize()

    def on_error(self, error: Any) -> None:
        input = self._input.dict()
        logger.error(f'Error in DiscordSendMessageProcessor: {error}')
        error_msg = '\n'.join(error.values()) if isinstance(
            error, dict) else 'Error in processing request'

        self._send_message(input['app_id'], error_msg, input['token'])

        async_to_sync(self._output_stream.write)(
            DiscordSendMessageOutput(code=200),
        )
        self._output_stream.finalize()

        return super().on_error(error)

    def get_bookkeeping_data(self) -> BookKeepingData:
        return BookKeepingData(input=self._input, timestamp=time.time(), run_data={'discord': {'user': self._input.discord_user_id, 'username': self._input.discord_username, 'global_name': self._input.discord_global_name}})
