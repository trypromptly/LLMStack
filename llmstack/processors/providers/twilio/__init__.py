from typing import List, Optional

from llmstack.processors.providers.api_processor_interface import ApiProcessorSchema


class TwilioSmsWebhookRequest(ApiProcessorSchema):
    ToCountry: Optional[str]
    ToState: Optional[str]
    SmsMessageSid: Optional[str]
    NumMedia: Optional[str]
    ToCity: Optional[str]
    FromZip: Optional[str]
    SmsSid: Optional[str]
    FromState: Optional[str]
    SmsStatus: Optional[str]
    FromCity: Optional[str]
    Body: Optional[str]
    FromCountry: Optional[str]
    To: Optional[str]
    ToZip: Optional[str]
    NumSegments: Optional[str]
    MessageSid: Optional[str]
    AccountSid: Optional[str]
    From: Optional[str]
    ApiVersion: Optional[str]
    input: Optional[str]
