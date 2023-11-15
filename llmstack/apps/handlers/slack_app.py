import logging
import re
import uuid

import requests

from llmstack.apps.handlers.app_runnner import AppRunner
from llmstack.play.actor import ActorConfig
from llmstack.play.actors.bookkeeping import BookKeepingActor
from llmstack.play.actors.input import InputActor
from llmstack.play.actors.output import OutputActor
from llmstack.play.utils import convert_template_vars_from_legacy_format
from llmstack.processors.providers.slack.post_message import SlackPostMessageProcessor

from django.contrib.auth.models import User, AnonymousUser

logger = logging.getLogger(__name__)


def generate_uuid(input_str):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, input_str))


def process_slack_message_text(text):
    return re.sub(r'<@.*>(\|)?', '', text).strip()


def get_slack_user_email(slack_user_id, slack_bot_token):
    http_request = requests.get(
        'https://slack.com/api/users.info', params={
            'user': slack_user_id,
        }, headers={'Authorization': f'Bearer {slack_bot_token}'},
    )
    if http_request.status_code == 200:
        return http_request.json()['user']['profile']['email']
    else:
        return None


class SlackAppRunner(AppRunner):

    def app_init(self):
        self.slack_bot_token = self.slack_config.get('bot_token')
        self.stream = False
        self.app_run_request_user = self._get_app_request_user(
           self.request_input_data,
        )
        self.session_id = self._get_slack_app_seession_id(self.request_input_data)
        self.app_session = self._get_or_create_app_session()

    def _get_app_request_user(self, slack_request_payload):
        self._slack_user_email = ''
        if 'event' in slack_request_payload and 'user' in slack_request_payload['event']:
            try:
                slack_user_id = slack_request_payload['event']['user']
                slack_user_email = get_slack_user_email(
                    slack_user_id, self.slack_bot_token,
                )
                if slack_user_email is not None:
                    self._slack_user_email = slack_user_email
                    user_object = User.objects.get(email=slack_user_email)
                    return user_object if user_object is not None else AnonymousUser()
            except Exception as e:
                logger.exception(
                    f"Error in fetching user object from slack payload {slack_request_payload}")

        return AnonymousUser()

    def _get_slack_app_seession_id(self, slack_request_payload):
        if slack_request_payload['type'] == 'event_callback' and 'event' in slack_request_payload:
            thread_ts = None
            session_identifier = None
            if 'thread_ts' in slack_request_payload['event']:
                thread_ts = slack_request_payload['event']['thread_ts']
            elif 'ts' in slack_request_payload['event']:
                thread_ts = slack_request_payload['event']['ts']

            if 'channel' in slack_request_payload['event']:
                session_identifier = f"{slack_request_payload['event']['channel']}_{thread_ts}"
            else:
                session_identifier = f"{slack_request_payload['event']['user']}_{thread_ts}"
            return generate_uuid(session_identifier)

        return None

    def _is_slack_url_verification_request(self):
        return self.request_input_data.get('type') == 'url_verification'

    def _get_input_data(self, slack_request_payload):
        slack_message_type = slack_request_payload['type']
        if slack_message_type == 'url_verification':
            return {'input': {'challenge': slack_request_payload['challenge']}}
        elif slack_message_type == 'event_callback':
            payload = process_slack_message_text(
                slack_request_payload['event']['text'],
            )
            return {
                'input': {
                    'text': slack_request_payload['event']['text'],
                    'user': slack_request_payload['event']['user'],
                    'slack_user_email': self._slack_user_email,
                    'token': slack_request_payload['token'],
                    'team_id': slack_request_payload['team_id'],
                    'api_app_id': slack_request_payload['api_app_id'],
                    'team': slack_request_payload['event']['team'],
                    'channel': slack_request_payload['event']['channel'],
                    'text-type': slack_request_payload['event']['type'],
                    'ts': slack_request_payload['event']['ts'],
                    **dict(zip(list(map(lambda x: x['name'], self.app_data['input_fields'])), [payload] * len(self.app_data['input_fields']))),
                },
            }
        else:
            raise Exception('Invalid Slack message type')

    def _get_slack_processor_actor_configs(self, input_data):
        output_template = convert_template_vars_from_legacy_format(
            self.app_data['output_template'].get(
                'markdown', '') if self.app_data and 'output_template' in self.app_data else self.app.output_template.get('markdown', ''),
        )
        vendor_env = self.app_owner_profile.get_vendor_env()

        return ActorConfig(
            name='slack_processor',
            template_key='slack_processor',
            actor=SlackPostMessageProcessor, kwargs={
                'env': vendor_env,
                'input': {
                    'slack_user': input_data['input']['user'],
                    'slack_user_email': input_data['input']['slack_user_email'],
                    'token': self.slack_bot_token,
                    'channel': input_data['input']['channel'],
                    'response_type': 'text',
                    'text': output_template,
                    'thread_ts': input_data['input']['ts'],
                },
                'config': {},
                'session_data': {},
            },
            output_cls=SlackPostMessageProcessor.get_output_cls(),
        )

    def _is_app_accessible(self):
        # Verify the request type is either url_verification or event_callback
        if self.request_input_data.get('type') not in ['event_callback', 'url_verification']:
            raise Exception('Invalid Slack request')

        # Verify the request is coming from the app we expect and the event type is app_mention
        if self.request_input_data.get('type') == 'event_callback' and (self.request_input_data.get('api_app_id') != self.slack_config.get('app_id') or self.request_input_data.get('event').get('type') != 'app_mention'):
            raise Exception('Invalid Slack request')

        # URL verification is allowed without any further checks
        if self.request_input_data.get('type') == 'url_verification':
            return True

        return super()._is_app_accessible()

    def run_app(self):
        # Check if the app access permissions are valid
        self._is_app_accessible()
        debug_data = []

        csp = 'frame-ancestors self'
        input_data = self._get_input_data(self.request_input_data)
        # Actor configs
        if self._is_slack_url_verification_request():
            template = '{"challenge": "{{_inputs0.challenge}}"}'
            actor_configs = [
                ActorConfig(
                    name='input', template_key='_inputs0', actor=InputActor, kwargs={'input_request': self.input_actor_request},
                ),
                ActorConfig(
                    name='output', template_key='output',
                    actor=OutputActor, kwargs={'template': template},
                ),
            ]
            processor_configs = {}
        else:
            template = convert_template_vars_from_legacy_format(
                self.app_data['output_template'].get(
                    'markdown', '') if self.app_data and 'output_template' in self.app_data else self.app.output_template.get('markdown', ''),
            )
            actor_configs = [
                ActorConfig(
                    name='input', template_key='_inputs0', actor=InputActor, kwargs={'input_request': self.input_actor_request},
                ),
                ActorConfig(
                    name='output', template_key='output',
                    actor=OutputActor, dependencies=['input'],
                    kwargs={'template': '{{_inputs0.user}}'},
                ),
            ]

            processor_actor_configs, processor_configs = self._get_processor_actor_configs()
            # Add our slack processor responsible to sending the outgoing message
            processor_actor_configs.append(
                self._get_slack_processor_actor_configs(input_data),
            )
            actor_configs.extend(processor_actor_configs)

            actor_configs.append(
                ActorConfig(
                    name='bookkeeping', template_key='bookkeeping', actor=BookKeepingActor, dependencies=['_inputs0', 'output', 'slack_processor'], kwargs={'processor_configs': processor_configs},
                ),
            )

        output = self._start(
            input_data, self.app_session,
            actor_configs, csp, template,
        )

        if self._is_slack_url_verification_request():
            return output
        else:
            return {}
