import logging
import uuid

from apps.apis import AppRunnerException
from apps.handlers.app_runnner import AppRunner
from apps.models import AppVisibility
from play.actor import ActorConfig
from play.actors.bookkeeping import BookKeepingActor
from play.actors.input import InputActor
from play.actors.output import OutputActor
from play.utils import convert_template_vars_from_legacy_format
from processors.providers.discord.send_message import DiscordSendMessageProcessor

logger = logging.getLogger(__name__)


class InvalidDiscordRequestSignature(AppRunnerException):
    status_code = 401
    details = 'Invalid Discord request signature'


def generate_uuid(input_str):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, input_str))


def process_discord_message_text(text):
    return text.strip()


class DiscordBotRunner(AppRunner):

    def app_init(self):
        self.discord_bot_token = self.discord_config.get('bot_token')
        self.session_id = self._get_discord_bot_seession_id(self.request.data)
        self._input_field_name = self.app.input_schema.get(
            'required', ['question'],
        )[0]

    def _get_discord_bot_seession_id(self, discord_request_payload):
        if 'id' in discord_request_payload:
            return generate_uuid(discord_request_payload['id'])
        return None

    def _get_input_data(self, discord_request_payload):
        discord_message_type = discord_request_payload['type']
        if discord_message_type == 1:
            return {
                'input': {
                    'token': discord_request_payload['token'],
                    'type': 1,
                },
            }
        else:
            if discord_message_type == 2 and discord_request_payload['data']['name'] == self.discord_config['slash_command_name']:
                app_input = {}

                for option in discord_request_payload['data']['options']:
                    app_input[option['name']] = option['value']

                return {
                    'input': {
                        'user': discord_request_payload['member']['user']['id'],
                        'username': discord_request_payload['member']['user']['username'],
                        'global_name': discord_request_payload['member']['user']['global_name'],
                        'channel': discord_request_payload['channel_id'],
                        'guild_id': discord_request_payload['guild_id'],
                        'token': discord_request_payload['token'],
                        **app_input,
                    },
                }

        raise Exception('Invalid Discord request')

    def _get_discord_processor_actor_configs(self, input_data):
        output_template = convert_template_vars_from_legacy_format(
            self.app.output_template.get('markdown', ''),
        )

        vendor_env = self.app_owner_profile.get_vendor_env()

        processors = [
            x.exit_endpoint for x in self.app.run_graph.all().order_by(
            'id',
            ) if x is not None and x.exit_endpoint is not None
        ]

        return ActorConfig(
            name='discord_processor',
            template_key='discord_processor',
            actor=DiscordSendMessageProcessor, kwargs={
                'env': vendor_env,
                'input': {
                    'discord_user_id': input_data['input']['user'],
                    'discord_username': input_data['input']['username'],
                    'discord_global_name': input_data['input']['global_name'],
                    'token': input_data['input']['token'],
                    'bot_token': self.discord_bot_token,
                    'channel_id': input_data['input']['channel'],
                    'text': output_template,
                    'app_id': self.discord_config['app_id'],
                },
                'config': {},
                'session_data': {},
            },
            output_cls=DiscordSendMessageProcessor.get_output_cls(),
        )

    def _is_app_accessible(self):
        if self.app.visibility != AppVisibility.PUBLIC:
            raise Exception('Invalid app visibility for discord app')

        return super()._is_app_accessible()

    def _is_discord_url_verification_request(self):
        return self.request.data.get('type') == 1

    def run_app(self):
        # Check if the app access permissions are valid
        try:
            self._is_app_accessible()
        except InvalidDiscordRequestSignature:
            logger.error('Invalid Discord request signature')
            raise e
        except Exception as e:
            logger.exception('Error while validating app access permissions')
            return {'type': 4, 'data': {'content': str(e)}}

        csp = 'frame-ancestors self'
        input_data = self._get_input_data(self.request.data)
        if self._is_discord_url_verification_request():
            template = '{"type": "{{_inputs0.type}}"}'
            actor_configs = [
                ActorConfig(
                    name='input', template_key='_inputs0', actor=InputActor, kwargs={'input_request': self.input_actor_request},
                ),
                ActorConfig(
                    name='output', template_key='output',
                    actor=OutputActor, kwargs={'template': '{"type": "{{_inputs0.type}}"}'},
                ),
            ]
            processor_configs = {}
        else:
            template = convert_template_vars_from_legacy_format(
                self.app.output_template.get('markdown', ''),
            )
            actor_configs = [
                ActorConfig(
                    name='input', template_key='_inputs0', actor=InputActor, kwargs={'input_request': self.input_actor_request},
                ),
                ActorConfig(
                    name='output', template_key='output',
                    actor=OutputActor, kwargs={'template': '{{_inputs0.channel}}'},
                ),
            ]
            processor_actor_configs, processor_configs = self._get_processor_actor_configs()
            # Add our discord processor responsible for sending the outgoing message
            processor_actor_configs.append(
                self._get_discord_processor_actor_configs(input_data),
            )
            actor_configs.extend(processor_actor_configs)

            actor_configs.append(
                ActorConfig(
                name='bookkeeping', template_key='bookkeeping', actor=BookKeepingActor, dependencies=['_inputs0', 'output', 'discord_processor'], kwargs={'processor_configs': processor_configs},
                ),
            )

        self._start(
            input_data, self.app_session,
            actor_configs, csp, template,
        )

        if self._is_discord_url_verification_request():
            return {'type': 1}
        else:
            return {'type': 5}
