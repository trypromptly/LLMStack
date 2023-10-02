import json
import logging
import time
from typing import Any, Dict
from typing import List
from typing import Optional

from pydantic import Field
from asgiref.sync import async_to_sync


from llmstack.common.blocks.http import BearerTokenAuth, HttpAPIProcessor, HttpAPIProcessorInput, HttpMethod, JsonBody
from llmstack.play.actor import BookKeepingData
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface, ApiProcessorSchema

class TwilioCreateMessageInput(ApiProcessorSchema):
    body: Optional[str]
    from_: Optional[str]
    to: Optional[str]
    


class TwilioCreateMessageOutput(ApiProcessorSchema):
    response: dict

class TwilioCreateMessageConfiguration(ApiProcessorSchema):
    account_sid: Optional[str]
    auth_token: Optional[str]


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

    def _send_message(self, url:str, message: str, to_: str, from_: str, account_sid: str, auth_token:str) -> None:
        
        return {}

    def process(self) -> dict:
        _env = self._env
        input = self._input.dict()

        

        url = f'https://api.twilio.com/2010-04-01/Accounts/${self._config.account_sid}/Messages.json'

        self._send_message(url=url, message=input['body'], to_=input['to'], from_=input['from_'], account_sid=self._config.account_sid, auth_token=self._config.auth_token)
        async_to_sync(self._output_stream.write)(
            TwilioCreateMessageOutput(response={}),
        )

        return self._output_stream.finalize()

    def on_error(self, error: Any) -> None:
        input = self._input.dict()
        return super().on_error(error)

    def get_bookkeeping_data(self) -> BookKeepingData:
        return BookKeepingData(input=self._input, timestamp=time.time(), run_data={'twilio': {}})
