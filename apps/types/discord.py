import logging
from typing import Optional

import requests
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey
from pydantic import Field
from rest_framework.exceptions import NotAuthenticated

from apps.models import App
from apps.types.app_type_interface import AppTypeInterface
from apps.types.app_type_interface import BaseSchema

logger = logging.getLogger(__name__)


def get_discord_field_type(input_field_type: str) -> int:
    if input_field_type == 'number':
        return 4
    elif input_field_type == 'boolean':
        return 5
    return 3


class DiscordCommandOptionInputFieldMapping(BaseSchema):
    command_option_name: str
    input_field_name: str


class DiscordAppConfigSchema(BaseSchema):
    app_id: str = Field(
        title='App ID', description="App ID of the Discord app. Your application's ID can be found in the URL of the your application console.", required=True,
    )
    slash_command_name: str = Field(
        default='promptly',
        title='Slash Command Name', description='The name of the slash command that will be used to trigger the app.', required=True,
    )
    slash_command_description: str = Field(
        title='Slash Command Description', default='Promptly App',
        description='The description of the slash command that will be used to trigger the app.', required=True,
    )
    bot_token: str = Field(
        title='Bot Token', widget='password',
        description="Bot token of the Discord app. Your bot's token can be found in the Bot section of the your application console.", required=True,
    )
    public_key: str = Field(
        title='Public Key', widget='password', description='Public key of the Discord app. Your public key can be found in the Bot section of the your application console.', required=True,
    )
    slash_command_id: Optional[str] = Field(widget='hidden')


class DiscordApp(AppTypeInterface[DiscordAppConfigSchema]):
    @staticmethod
    def slug() -> str:
        return 'discord'

    @classmethod
    def pre_save(self, app: App):
        if app.is_published and app.discord_config:
            config = app.discord_config

            slash_command_name = config['slash_command_name']
            slash_command_options = []
            properties = app.input_schema['properties']

            for input_field in properties:
                slash_command_options.append({
                    'name': input_field,
                    'description': properties[input_field]['description'],
                    'type': get_discord_field_type(properties[input_field]['type']),
                    'required': input_field in app.input_schema.get('required', []),
                })
            body = {
                'name': slash_command_name,
                'type': 1,
                'description': config.get('slash_command_description', 'Promptly App'),
                'options': slash_command_options,
            }

            if config.get('slash_command_id'):
                # Update the slash command
                response = requests.patch(
                    f'https://discord.com/api/v10/applications/{config.get("app_id")}/commands/{config.get("slash_command_id")}', json=body, headers={
                        'Authorization': f'Bot {config.get("bot_token")}',
                    },
                )

            else:
                # Create the slash command
                response = requests.post(
                    f'https://discord.com/api/v10/applications/{config.get("app_id")}/commands', json=body, headers={
                        'Authorization': f'Bot {config.get("bot_token")}',
                    },
                )
                config['slash_command_id'] = response.json()['id']
                app.discord_config = config

        return app

    @classmethod
    def verify_request_signature(cls, app: App, headers: dict, raw_body: bytes):
        signature = headers.get('X-Signature-Ed25519')
        timestamp = headers.get('X-Signature-Timestamp')

        if signature and timestamp and raw_body:
            public_key = app.discord_config.get('public_key')
            verify_key = VerifyKey(bytes.fromhex(public_key))
            try:
                verify_key.verify(
                    f'{timestamp}{raw_body.decode("utf-8")}'.encode(),
                    bytes.fromhex(signature),
                )
            except BadSignatureError:
                logger.error('Request signature verification failed')
                raise NotAuthenticated()
        return True
