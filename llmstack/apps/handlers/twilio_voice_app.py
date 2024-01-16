import base64
import uuid
import logging

import requests

from llmstack.apps.handlers.app_runnner import AppRunner
from llmstack.apps.models import AppVisibility
from llmstack.common.utils.audio_loader import partition_audio
from llmstack.common.utils.text_extract import ExtraParams, extract_text_elements
from llmstack.play.actor import ActorConfig
from llmstack.play.actors.bookkeeping import BookKeepingActor
from llmstack.play.actors.input import InputActor
from llmstack.play.actors.output import OutputActor
from llmstack.play.utils import convert_template_vars_from_legacy_format
from llmstack.processors.providers.twilio.create_message import TwilioCreateMessageProcessor

logger = logging.getLogger(__name__)


def generate_uuid(input_str):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, input_str))


class TwilioVoiceAppRunner(AppRunner):
    def app_init(self):
        self.twilio_auth_token = self.twilio_config.get(
            'auth_token') if self.twilio_config else ''
        self.twilio_account_sid = self.twilio_config.get(
            'account_sid') if self.twilio_config else ''
        self.twilio_phone_numbers = self.twilio_config.get(
            'phone_numbers') if self.twilio_config else ''

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
        vendor_env = self.app_owner_profile.get_vendor_env()

        input_data = {
            '_request': {
                'CallSid': twilio_request_payload.get('CallSid', ''),
                'CallStatus': twilio_request_payload.get('CallStatus', ''),
                'Called': twilio_request_payload.get('Called', ''),
                'CalledCity': twilio_request_payload.get('CalledCity', ''),
                'CalledCountry': twilio_request_payload.get('CalledCountry', ''),
                'CalledState': twilio_request_payload.get('CalledState', ''),
                'CalledZip': twilio_request_payload.get('CalledZip', ''),
                'Caller': twilio_request_payload.get('Caller', ''),
                'CallerCity': twilio_request_payload.get('CallerCity', ''),
                'CallerCountry': twilio_request_payload.get('CallerCountry', ''),
                'CallerState': twilio_request_payload.get('CallerState', ''),
                'CallerZip': twilio_request_payload.get('CallerZip', ''),
                'Digits': twilio_request_payload.get('Digits', ''),
                'Direction': twilio_request_payload.get('Direction', ''),
                'From': twilio_request_payload.get('From', ''),
                'FromCity': twilio_request_payload.get('FromCity', ''),
                'FromCountry': twilio_request_payload.get('FromCountry', ''),
                'FromState': twilio_request_payload.get('FromState', ''),
                'FromZip': twilio_request_payload.get('FromZip', ''),
                'RecordingDuration': twilio_request_payload.get('RecordingDuration', ''),
                'RecordingSid': twilio_request_payload.get('RecordingSid', ''),
                'RecordingUrl': twilio_request_payload.get('RecordingUrl', ''),
                'To': twilio_request_payload.get('To', ''),
                'ToCountry': twilio_request_payload.get('ToCountry', ''),
                'ToState': twilio_request_payload.get('ToState', ''),
                'ToCity': twilio_request_payload.get('ToCity', ''),
                'AccountSid': twilio_request_payload.get('AccountSid', ''),
                'ApiVersion': twilio_request_payload.get('ApiVersion', ''),
            },
        }
        recording_url = twilio_request_payload.get('RecordingUrl', None)
        if recording_url is None:
            raise Exception(
                'Recording url not found in twilio request payload')
        if not recording_url.endswith('.mp3'):
            recording_url = recording_url + '.mp3'
            recording_filename = recording_url.split('/')[-1]
        response = requests.get(
            recording_url,
            auth=(
                self.twilio_account_sid,
                self.twilio_auth_token))
        if response.status_code == 200:
            mp3_content = response.content
            # Encode the MP3 content as a base64 data URI
            data_uri = f'data:audio/mp3;name={recording_filename};base64,' + \
                base64.b64encode(mp3_content).decode()
        else:
            raise Exception('Error while downloading recording from twilio')

        recording_text = '\n\n'.join(
            [
                str(el) for el in extract_text_elements(
                    'audio/mp3',
                    mp3_content,
                    recording_filename,
                    extra_params=ExtraParams(
                        openai_key=vendor_env.get(
                            'openai_api_key',
                            None)))])

        return {'input': {**input_data,
                          'recording': data_uri,
                          'recording_transcription': recording_text,
                          **dict(zip(list(map(lambda x: x['name'],
                                              self.app_data['input_fields'])),
                                     [recording_text] * len(self.app_data['input_fields']))),
                          },
                }

    def _get_twilio_processor_actor_configs(self, input_data):
        vendor_env = self.app_owner_profile.get_vendor_env()
        output_template = convert_template_vars_from_legacy_format(
            self.app_data['output_template'].get(
                'markdown',
                '') if self.app_data and 'output_template' in self.app_data else self.app.output_template.get(
                'markdown',
                ''),
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
                'markdown',
                '') if self.app_data and 'output_template' in self.app_data else self.app.output_template.get(
                'markdown',
                ''),
        )

        actor_configs = [
            ActorConfig(
                name='input',
                template_key='_inputs0',
                actor=InputActor,
                kwargs={
                    'input_request': self.input_actor_request},
            ),
            ActorConfig(
                name='output',
                template_key='output',
                dependencies=['input'],
                actor=OutputActor,
                kwargs={
                    'template': '{{_inputs0._request}}'},
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
                name='bookkeeping',
                template_key='bookkeeping',
                actor=BookKeepingActor,
                dependencies=[
                    '_inputs0',
                    'output',
                    'twilio_processor'],
                kwargs={
                    'processor_configs': processor_configs}))

        self._start(
            input_data, self.app_session,
            actor_configs, csp, template,
        )
        return {}
