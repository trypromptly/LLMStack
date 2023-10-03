from typing import Any
import uuid
import logging

from llmstack.apps.handlers.app_runnner import AppRunner
from llmstack.apps.handlers.twilio_utils import RequestValidator
from llmstack.apps.models import AppVisibility
from llmstack.play.actor import ActorConfig
from llmstack.play.actors.bookkeeping import BookKeepingActor
from llmstack.play.actors.input import InputActor
from llmstack.play.actors.output import OutputActor
from llmstack.play.utils import convert_template_vars_from_legacy_format
from llmstack.processors.providers.twilio.create_message import TwilioCreateMessageProcessor

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
    def app_init(self):
        self.twilio_auth_token = self.twilio_config.get('auth_token') if self.twilio_config else ''
        self.twilio_account_sid = self.twilio_config.get('account_sid') if self.twilio_config else ''
        self.twilio_phone_numbers = self.twilio_config.get('phone_numbers') if self.twilio_config else ''
            
        self.session_id = self._get_twilio_app_seession_id(self.request.data)
    
    def _get_twilio_app_seession_id(self, twilio_request_payload):
        if 'id' in twilio_request_payload:
            return generate_uuid(twilio_request_payload['id'])
        return None
    
    def _is_app_accessible(self):
        if self.app.visibility != AppVisibility.PUBLIC:
            raise Exception('Invalid app visibility for discord app')
        return super()._is_app_accessible()
    
    def _get_input_data(self, twilio_request_payload):
        
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
                 **dict(zip(list(map(lambda x: x['name'], self.app_data['input_fields'])), [twilio_request_payload.get('Body', '')] * len(self.app_data['input_fields']) )),
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
    
    def run_app(self):
        # Check if the app access permissions are valid
        try:
            self._is_app_accessible()
        except Exception as e:
            logger.exception('Error while validating app access permissions')
            return {}

        csp = 'frame-ancestors self'
        input_data = self._get_input_data(self.request.data)
        
        template = convert_template_vars_from_legacy_format(
                self.app_data['output_template'].get(
                    'markdown', '') if self.app_data and 'output_template' in self.app_data else self.app.output_template.get('markdown', ''),
            )
        
        actor_configs = [
            ActorConfig(
                name='input', template_key='_inputs0', actor=InputActor, kwargs={'input_request': self.input_actor_request},
                ),
            ActorConfig(
                name='output', template_key='output',  dependencies=['input'],
                actor=OutputActor, kwargs={'template': '{{_inputs0._request}}'},
                ),
            ]
        processor_actor_configs, processor_configs = self._get_processor_actor_configs()
        
        # Add our twilio processor responsible for sending the outgoing message
        processor_actor_configs.append(
            self._get_twilio_processor_actor_configs(input_data),
            )
        actor_configs.extend(processor_actor_configs)

        actor_configs.append(
            ActorConfig(
                name='bookkeeping', template_key='bookkeeping', actor=BookKeepingActor, dependencies=['_inputs0', 'output', 'twilio_processor'], kwargs={'processor_configs': processor_configs})
            )

        self._start(
            input_data, self.app_session,
            actor_configs, csp, template,
        )
        return {}