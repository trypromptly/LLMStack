import logging
from typing import List

from pydantic import Field
import requests
from llmstack.apps.models import App
from llmstack.apps.types.app_type_interface import AppTypeInterface, BaseSchema

logger = logging.getLogger(__name__)


class TwilioSmsAppConfigSchema(BaseSchema):
    account_sid: str = Field(
        title='Account SID', description="Account SID of the Twilio account. Your account's SID can be found in the console.", required=True,
    )
    auth_token: str = Field(
        title='Auth Token', widget='password',
        description="Auth token of the Twilio account. Your account's auth token can be found in the console.", required=True,
    )
    phone_numbers: List[str] = Field(
        title='Phone Numbers', description='Phone numbers to send SMS messages from.', required=True,
    )
    auto_create_sms_webhook: bool = Field(default=False, title='Auto Create SMS Webhook',
                                          description='Automatically create an SMS webhook for the phone numbers.', required=False,
                                          )


class TwilioSmsApp(AppTypeInterface[TwilioSmsAppConfigSchema]):
    @staticmethod
    def slug() -> str:
        return 'twilio_sms'

    @staticmethod
    def name() -> str:
        return 'Twilio SMS App'

    @staticmethod
    def description() -> str:
        return 'Send SMS messages from Twilio.'

    @classmethod
    def pre_save(self, app: App):
        if app.is_published and app.twilio_config:
            config = app.twilio_config
            auto_create_sms_webhook = config.get(
                'auto_create_sms_webhook', False)

            if auto_create_sms_webhook:
                phone_numbers = config.get('phone_numbers', [])
                account_sid = config.get('account_sid', None)
                auth_token = config.get('auth_token', None)

                if not phone_numbers:
                    raise Exception(
                        'You must provide at least one phone number to send SMS messages from.')
                if not account_sid or not auth_token:
                    raise Exception(
                        'You must provide an account SID and auth token to send SMS messages from.')

                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                }
                auth = (account_sid, auth_token)
                for phone_number in phone_numbers:
                    ph_no = phone_number.strip().replace('+', '').replace('-', '')
                    response = requests.get(
                        f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/IncomingPhoneNumbers.json?PhoneNumber=%2B{ph_no}',
                        headers=headers, auth=auth)
                    if response.status_code != 200:
                        raise Exception(
                            f'Invalid phone number {phone_number}. Please provide a valid phone number that you own.')

                    if 'incoming_phone_numbers' in response.json() and len(response.json()['incoming_phone_numbers']) > 0:
                        twilio_phone_number_resource = response.json()[
                            'incoming_phone_numbers'][0]
                        sms_url = twilio_phone_number_resource['sms_url']
                        # Create SMS webhook if it doesn't exist
                        if (not sms_url or sms_url != f'https://trypromptly.com/api/apps/{app.uuid}/twiliosms/run'):
                            # Update twilio phone number resource with voice webhook
                            response = requests.post(
                                f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/IncomingPhoneNumbers/{twilio_phone_number_resource["sid"]}.json',
                                headers=headers, auth=auth, data={
                                    'SmsUrl': f'https://trypromptly.com/api/apps/{app.uuid}/twiliosms/run',
                                })
                            if response.status_code != 200:
                                raise Exception(
                                    f'Failed to update SMS webhook for phone number {phone_number}. Error: {response.text}')

        return app
