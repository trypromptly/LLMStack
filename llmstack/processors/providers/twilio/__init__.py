from typing import Optional

from llmstack.processors.providers.api_processor_interface import ApiProcessorSchema


class TwilioSmsWebhookRequest(ApiProcessorSchema):
    ToCountry: Optional[str] = None
    ToState: Optional[str] = None
    SmsMessageSid: Optional[str] = None
    NumMedia: Optional[str] = None
    ToCity: Optional[str] = None
    FromZip: Optional[str] = None
    SmsSid: Optional[str] = None
    FromState: Optional[str] = None
    SmsStatus: Optional[str] = None
    FromCity: Optional[str] = None
    Body: Optional[str] = None
    FromCountry: Optional[str] = None
    To: Optional[str] = None
    ToZip: Optional[str] = None
    NumSegments: Optional[str] = None
    MessageSid: Optional[str] = None
    AccountSid: Optional[str] = None
    From: Optional[str] = None
    ApiVersion: Optional[str] = None
    input: Optional[str] = None
