import logging
import uuid
from typing import Any

from llmstack.apps.app_session_utils import (
    create_agent_app_session_data,
    get_agent_app_session_data,
)
from llmstack.apps.handlers.app_runnner import AppRunner
from llmstack.apps.handlers.twilio_utils import RequestValidator
from llmstack.apps.integration_configs import TwilioIntegrationConfig
from llmstack.apps.models import AppVisibility
from llmstack.play.actor import ActorConfig
from llmstack.play.actors.agent import AgentActor
from llmstack.play.actors.bookkeeping import BookKeepingActor
from llmstack.play.actors.input import InputActor
from llmstack.play.actors.output import OutputActor
from llmstack.play.utils import convert_template_vars_from_legacy_format
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface
from llmstack.processors.providers.twilio.create_message import (
    TwilioCreateMessageProcessor,
)

logger = logging.getLogger(__name__)


def generate_uuid(input_str):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, input_str))


def verify_request_signature(app: Any, base_url: str, headers: dict, raw_body: bytes):
    signature = headers.get('X-TWILIO-SIGNATURE')
    if not signature:
        return False

    validator = RequestValidator(app.twilio_config.auth_token)
    request_valid = validator.validate(
        f'{base_url}/api/apps/{str(app.uuid)}/twiliosms/run',
        'POST',
        signature)
    if not request_valid:
        return False
    return True


class TwilioSmsAppRunner(AppRunner):
    def _get_processors_as_functions(self):
        functions = []
        processor_classes = {}

        for processor_class in ApiProcessorInterface.__subclasses__():
            processor_classes[(processor_class.provider_slug(),
                               processor_class.slug())] = processor_class

        for processor in self.app_data['processors'] if self.app_data and 'processors' in self.app_data else []:
            if (processor['provider_slug'], processor['processor_slug']) not in processor_classes:
                continue
            functions.append({
                'name': processor['id'],
                'description': processor['description'],
                'parameters': processor_classes[(processor['provider_slug'], processor['processor_slug'])].get_tool_input_schema(processor),
            })
        return functions

    def app_init(self):
        self.twilio_config = TwilioIntegrationConfig().from_dict(
            self.app.twilio_integration_config,
            self.app_owner_profile.decrypt_value,
        ) if self.app.twilio_integration_config else None
        
        self.twilio_auth_token = self.twilio_config.get(
            'auth_token') if self.twilio_config else ''
        self.twilio_account_sid = self.twilio_config.get(
            'account_sid') if self.twilio_config else ''
        self.twilio_phone_numbers = self.twilio_config.get(
            'phone_numbers') if self.twilio_config else ''

        self.session_id = self._get_twilio_app_seession_id(self.request.data)

    def _get_twilio_app_seession_id(self, twilio_request_payload):
        if 'From' in twilio_request_payload:
            id = f'{str(self.app.uuid)}-{twilio_request_payload["From"]}'
            return generate_uuid(id)
        return None

    def _is_app_accessible(self):
        if self.app.visibility != AppVisibility.PUBLIC:
            raise Exception('Invalid app visibility for discord app')
        return super()._is_app_accessible()

    def _get_input_data(self):
        twilio_request_payload = self.request.data
        input_data = {
            '_request': {
                'ToCountry': twilio_request_payload.get('ToCountry', ''),
                'ToState': twilio_request_payload.get('ToState', ''),
                'SmsMessageSid': twilio_request_payload.get('SmsMessageSid', ''),
                'NumMedia': twilio_request_payload.get('NumMedia', ''),
                'ToCity': twilio_request_payload.get('ToCity', ''),
                'FromZip': twilio_request_payload.get('FromZip', ''),
                'SmsSid': twilio_request_payload.get('SmsSid', ''),
                'FromState': twilio_request_payload.get('FromState', ''),
                'SmsStatus': twilio_request_payload.get('SmsStatus', ''),
                'FromCity': twilio_request_payload.get('FromCity', ''),
                'Body': twilio_request_payload.get('Body', ''),
                'FromCountry': twilio_request_payload.get('FromCountry', ''),
                'To': twilio_request_payload.get('To', ''),
                'ToZip': twilio_request_payload.get('ToZip', ''),
                'NumSegments': twilio_request_payload.get('NumSegments', ''),
                'MessageSid': twilio_request_payload.get('MessageSid', ''),
                'AccountSid': twilio_request_payload.get('AccountSid', ''),
                'From': twilio_request_payload.get('From', ''),
                'ApiVersion': twilio_request_payload.get('ApiVersion', ''),
            },
        }

        return {
            'input': {
                **input_data,
                **dict(zip(list(map(lambda x: x['name'], self.app_data['input_fields'])), [twilio_request_payload.get('Body', '')] * len(self.app_data['input_fields']))),
            },
        }

    def _get_twilio_processor_actor_configs(self, input_data):
        vendor_env = self.app_owner_profile.get_vendor_env()
        output_template = convert_template_vars_from_legacy_format(
            self.app_data['output_template'].get(
                'markdown', '') if self.app_data and 'output_template' in self.app_data else self.app.output_template.get('markdown', ''),
        )

        return ActorConfig(
            name='twilio_processor',
            template_key='twilio_processor',
            actor=TwilioCreateMessageProcessor, kwargs={
                'env': vendor_env,
                'input': {
                    '_request': input_data['input']['_request'],
                    'body': output_template,
                    'to': input_data['input']['_request']['From'],
                },
                'config': {
                    'account_sid': self.twilio_account_sid,
                    'auth_token': self.twilio_auth_token,
                    'phone_number': input_data['input']['_request']['To'],
                },
                'session_data': {},
            },
            output_cls=TwilioCreateMessageProcessor.get_output_cls(),
        )

    def _get_csp(self):
        return 'frame-ancestors self'
    
    def _get_bookkeeping_actor_config(self, processor_configs):
        if self.app.type.slug == 'agent':
            return ActorConfig(
                name='bookkeeping', template_key='bookkeeping', 
                actor=BookKeepingActor,
                dependencies=['_inputs0', 'output', 'twilio_processor', 'agent'], 
                kwargs={'processor_configs': processor_configs, 'is_agent': True},
            )
        else:
            return ActorConfig(
                name='bookkeeping', template_key='bookkeeping', 
                actor=BookKeepingActor, dependencies=['_inputs0', 'output', 'twilio_processor'], 
                kwargs={'processor_configs': processor_configs},
            )
    
    def _get_base_actor_configs(self, output_template, processor_configs):
        actor_configs = []
        if self.app.type.slug == 'agent':
            input_data = self._get_input_data()
            agent_app_session_data = get_agent_app_session_data(self.app_session)
            if not agent_app_session_data:
                agent_app_session_data = create_agent_app_session_data(self.app_session, {})
            actor_configs = [
                ActorConfig(
                    name='input', template_key='_inputs0', actor=InputActor, kwargs={'input_request': self.input_actor_request},
                ),
                ActorConfig(
                    name='agent', template_key='agent', 
                    actor=AgentActor, 
                    kwargs={
                            'processor_configs': processor_configs, 
                            'functions': self._get_processors_as_functions(), 
                            'input': input_data.get('input', {}), 'env': self.app_owner_profile.get_vendor_env(), 
                            'config': self.app_data['config'],
                            'agent_app_session_data': agent_app_session_data,
                            }
                ),
                ActorConfig(
                    name='output', template_key='output',
                    dependencies=['_inputs0'],
                    actor=OutputActor, kwargs={'template': '{{_inputs0}}'}
                ),
            ]
        else:
            actor_configs = [
                ActorConfig(
                    name='input', template_key='_inputs0', actor=InputActor, kwargs={'input_request': self.input_actor_request}),
                ActorConfig(
                    name='output', template_key='output',  dependencies=['input'],
                    actor=OutputActor, kwargs={'template': '{{_inputs0}}'}
                    )
                ]
            
        return actor_configs
    
    def _get_actor_configs(self, template, processor_configs, processor_actor_configs):
        # Actor configs
        actor_configs = self._get_base_actor_configs(template, processor_configs)
        
        if self.app.type.slug == 'agent':
            actor_configs.extend(map(lambda x: ActorConfig(
            name=x.name, template_key=x.template_key, actor=x.actor, dependencies=(x.dependencies + ['agent']), kwargs=x.kwargs), processor_actor_configs)
        )
        else:
            actor_configs.extend(processor_actor_configs)
        
        # Add our twilio processor responsible for sending the outgoing message
        actor_configs.append(self._get_twilio_processor_actor_configs(self._get_input_data()))
        actor_configs.append(self._get_bookkeeping_actor_config(processor_configs))
        return actor_configs