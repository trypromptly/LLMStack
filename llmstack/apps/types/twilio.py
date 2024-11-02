import logging
from typing import List

import requests
from django.conf import settings
from pydantic import Field

from llmstack.apps.models import App
from llmstack.apps.types.app_type_interface import AppTypeInterface, BaseSchema

logger = logging.getLogger(__name__)


class TwilioAppConfigSchema(BaseSchema):
    account_sid: str = Field(
        title="Account SID",
        description="Account SID of the Twilio account. Your account's SID can be found in the console.",
    )
    auth_token: str = Field(
        title="Auth Token",
        json_schema_extra={"widget": "password"},
        description="Auth token of the Twilio account. Your account's auth token can be found in the console.",
    )
    phone_numbers: List[str] = Field(
        title="Phone Numbers",
        description="Phone numbers to send SMS messages from.",
    )
    auto_create_sms_webhook: bool = Field(
        default=False,
        title="Auto Create SMS Webhook",
        description="Automatically create an SMS webhook for the phone numbers.",
        json_schema_extra={"required": False},
    )
    auto_create_voice_webhook: bool = Field(
        default=False,
        title="Auto Create Voice Webhook",
        description="Automatically create a voice webhook for the phone numbers.",
        json_schema_extra={"required": False},
    )


class TwilioApp(AppTypeInterface[TwilioAppConfigSchema]):
    @staticmethod
    def slug() -> str:
        return "twilio"

    @staticmethod
    def name() -> str:
        return "Twilio App"

    @staticmethod
    def description() -> str:
        return "Send SMS and voice messages from Twilio."

    @classmethod
    def pre_save(self, app: App):
        if app.is_published and app.twilio_config:
            config = app.twilio_config
            auto_create_sms_webhook = config.get(
                "auto_create_sms_webhook",
                False,
            )
            auto_create_voice_webhook = config.get(
                "auto_create_voice_webhook",
                False,
            )

            if auto_create_sms_webhook or auto_create_voice_webhook:
                phone_numbers = config.get("phone_numbers", [])
                account_sid = config.get("account_sid", None)
                auth_token = config.get("auth_token", None)

                if not phone_numbers:
                    raise Exception(
                        "You must provide at least one phone number to configure webhooks for.",
                    )
                if not account_sid or not auth_token:
                    raise Exception(
                        "You must provide an account SID and auth token to configure webhooks.",
                    )

                headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                }
                auth = (account_sid, auth_token)
                for phone_number in phone_numbers:
                    ph_no = phone_number.strip().replace("+", "").replace("-", "")
                    response = requests.get(
                        f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/IncomingPhoneNumbers.json?PhoneNumber=%2B{ph_no}",
                        headers=headers,
                        auth=auth,
                    )
                    if response.status_code != 200:
                        raise Exception(
                            f"Invalid phone number {phone_number}. Please provide a valid phone number that you own.",
                        )

                    if (
                        "incoming_phone_numbers" in response.json()
                        and len(
                            response.json()["incoming_phone_numbers"],
                        )
                        > 0
                    ):
                        twilio_phone_number_resource = response.json()["incoming_phone_numbers"][0]
                        update_data = {}

                        if auto_create_sms_webhook:
                            sms_url = twilio_phone_number_resource["sms_url"]
                            webhook_url = f"{settings.SITE_URL}/api/apps/{app.uuid}/twiliosms/run"
                            if not sms_url or sms_url != webhook_url:
                                update_data["SmsUrl"] = webhook_url

                        if auto_create_voice_webhook and app.type_slug == "voice-agent":
                            voice_url = twilio_phone_number_resource["voice_url"]
                            webhook_url = f"{settings.SITE_URL}/api/apps/{app.uuid}/twiliovoice/run"
                            if not voice_url or voice_url != webhook_url:
                                update_data["VoiceUrl"] = webhook_url

                        if update_data:
                            response = requests.post(
                                f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/IncomingPhoneNumbers/{twilio_phone_number_resource["sid"]}.json',
                                headers=headers,
                                auth=auth,
                                data=update_data,
                            )
                            if response.status_code != 200:
                                raise Exception(
                                    f"Failed to update webhooks for phone number {phone_number}. Error: {response.text}",
                                )

        return app
