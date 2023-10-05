import logging
import time
from typing import Any
from typing import Optional

from asgiref.sync import async_to_sync
from llmstack.common.blocks.http import BasicAuth, HttpAPIProcessor, HttpAPIProcessorInput, HttpMethod, FormBody

from llmstack.play.actor import BookKeepingData
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface, ApiProcessorSchema
from llmstack.processors.providers.twilio import TwilioSmsWebhookRequest

logger = logging.getLogger(__name__)



class TwilioCreateMessageInput(ApiProcessorSchema):
    _request: Optional[TwilioSmsWebhookRequest]
    body: Optional[str]
    to: Optional[str]

class TwilioCreateMessageOutput(ApiProcessorSchema):
    response: dict

class TwilioCreateMessageConfiguration(ApiProcessorSchema):
    account_sid: Optional[str]
    auth_token: Optional[str]
    phone_number: Optional[str]

class TwilioCreateMessageProcessor(ApiProcessorInterface[TwilioCreateMessageInput, TwilioCreateMessageOutput, TwilioCreateMessageConfiguration]):
    """
    Twilio Create Message API
    """
    @staticmethod
    def name() -> str:
        return 'twilio/create_message'

    @staticmethod
    def slug() -> str:
        return 'create_message'

    @staticmethod
    def description() -> str:
        return 'Creates a message on Twilio'

    @staticmethod
    def provider_slug() -> str:
        return 'twilio'

    def _send_message(self, message: str, to_: str, from_: str, account_sid: str, auth_token:str) -> None:
        #Send a message to a phone number
        url = f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json'
        http_processor = HttpAPIProcessor(configuration={'timeout': 60})
        input = HttpAPIProcessorInput(
                url=url,
                method=HttpMethod.POST,
                headers={},
                authorization=BasicAuth(username=account_sid, password=auth_token),
                body=FormBody(form_body={
                    'To': to_,
                    'From': from_,
                    'Body': message
                }),
                )
        response = http_processor.process(input.dict()).dict()
        return response

        

    def process(self) -> dict:
        input = self._input.dict()
        response = self._send_message(message=input['body'], to_=input['to'], from_=self._config.phone_number, account_sid=self._config.account_sid, auth_token=self._config.auth_token)
        async_to_sync(self._output_stream.write)(
            TwilioCreateMessageOutput(response=response),
        )
        return self._output_stream.finalize()

    def on_error(self, error: Any) -> None:
        input = self._input.dict()

        logger.error(f'Error in TwilioCreateMessageProcessor: {error}')
        
        error_msg = '\n'.join(error.values()) if isinstance(
            error, dict) else 'Error in processing request'

        response = self._send_message(
            error_msg, to_=input['to'], from_=self._config.phone_number, account_sid=self._config.account_sid, auth_token=self._config.auth_token)
        async_to_sync(self._output_stream.write)(
            TwilioCreateMessageOutput(response=response),
        )
        self._output_stream.finalize()
        return super().on_error(error)

    def get_bookkeeping_data(self) -> BookKeepingData:
        return BookKeepingData(input=self._input, timestamp=time.time(), run_data={'twilio': {'requestor' : self._input._request.From}})
