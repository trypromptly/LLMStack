import json
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import requests
from asgiref.sync import async_to_sync
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from pydantic import BaseModel
from pydantic import Field

from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface, ApiProcessorSchema

logger = logging.getLogger(__name__)


class Citation(BaseModel):
    startIndex: int
    endIndex: int
    url: str
    title: str
    license: str
    publicationDate: str


class CitationMetadata(BaseModel):
    citations: Optional[List[Citation]]


class SafetyAttributes(BaseModel):
    categories: Optional[List[str]]
    blocked: bool
    scores: List[float]


class TextChatContent(BaseModel):
    author: Optional[str] = Field(description='The author.')
    content: str = Field(description='The text.')


class TextChatExample(BaseModel):
    input: TextChatContent = Field(
        description='The text of the example.',
    )
    output: TextChatContent = Field(
        description='The text of the example.',
    )


class TextChatInput(ApiProcessorSchema):
    messages: List[TextChatContent] = Field(
        description='Conversation history provided to the model in a structured alternate-author form. Messages appear in chronological order: oldest first, newest last. When the history of messages causes the input to exceed the maximum length, the oldest messages are removed until the entire prompt is within the allowed limit.', default=[TextChatContent(content='', author='user')],
    )
    context: Optional[str] = Field(
        description='Context shapes how the model responds throughout the conversation. For example, you can use context to specify words the model can or cannot use, topics to focus on or avoid, or the response format or style.',
    )
    examples: Optional[List[TextChatExample]] = Field(
        description='List of structured messages to the model to learn how to respond to the conversation.', default=[TextChatExample(input=TextChatContent(content='Hello', author='user'), output=TextChatContent(content='Hi, how are you?', author='assistant'))],
    )


class TextChatPrediction(BaseModel):
    content: str = Field(description='Generated prediction content.')
    citationMetadata: Optional[CitationMetadata] = Field(
        description='Metadata for the citations found in the response.',
    )
    safetyAttributes: Optional[SafetyAttributes] = Field(
        description='Safety attributes for the response.',
    )


class TextChatOutput(ApiProcessorSchema):
    prediction: TextChatPrediction


class TextChatConfiguration(ApiProcessorSchema):
    temperature: float = Field(description='The temperature is used for sampling during the response generation, which occurs when topP and topK are applied. Temperature controls the degree of randomness in token selection. Lower temperatures are good for prompts that require a more deterministic and less open-ended or creative response, while higher temperatures can lead to more diverse or creative results. A temperature of 0 is deterministic: the highest probability response is always selected. For most use cases, try starting with a temperature of 0.2.', default=0.0, le=1.0, ge=0.0, multiple_of=0.1)
    maxOutputTokens: Optional[int] = Field(
        description='Maximum number of tokens that can be generated in the response. Specify a lower value for shorter responses and a higher value for longer responses.', le=1024, ge=1, default=256, multiple_of=1,
    )
    topK: Optional[int] = Field(description="Top-k changes how the model selects tokens for output. A top-k of 1 means the selected token is the most probable among all tokens in the model's vocabulary(also called greedy decoding), while a top-k of 3 means that the next token is selected from among the 3 most probable tokens(using temperature).", le=40, ge=1, default=40, multiple_of=1)
    topP: Optional[float] = Field(description="Top-p changes how the model selects tokens for output. Tokens are selected from most K(see topK parameter) probable to least until the sum of their probabilities equals the top-p value. For example, if tokens A, B, and C have a probability of 0.3, 0.2, and 0.1 and the top-p value is 0.5, then the model will select either A or B as the next token(using temperature) and doesn't consider C. The default top-p value is 0.95.", default=0.95)
    auth_token: Optional[str] = Field(description='Google API key.')
    project_id: Optional[str] = Field(description='Google project ID.')


class TextChatProcessor(ApiProcessorInterface[TextChatInput, TextChatOutput, TextChatConfiguration]):
    @staticmethod
    def name() -> str:
        return 'PaLM 2 For Chat'

    @staticmethod
    def slug() -> str:
        return 'text_chat'

    @staticmethod
    def description() -> str:
        return 'Chat completions from Google Vertex AI'

    @staticmethod
    def provider_slug() -> str:
        return 'google'

    def process(self) -> dict:
        token = None
        project_id = None
        google_service_account_json_key = json.loads(
            self._env.get('google_service_account_json_key', '{}'),
        )

        if self._config.project_id:
            project_id = self._config.project_id
        else:
            project_id = google_service_account_json_key.get(
                'project_id', None,
            )

        if self._config.auth_token:
            token = self._config.auth_token
        else:
            credentials = service_account.Credentials.from_service_account_info(
                google_service_account_json_key,
            )
            credentials = credentials.with_scopes(
                ['https://www.googleapis.com/auth/cloud-platform'],
            )
            credentials.refresh(Request())
            token = credentials.token

        if token is None:
            raise Exception('No auth token provided.')

        if project_id is None:
            raise Exception('No project ID provided.')

        api_url = f'https://us-central1-aiplatform.googleapis.com/v1/projects/{project_id}/locations/us-central1/publishers/google/models/chat-bison:predict'

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json; charset=utf-8',
        }
        input_instance = self._input.dict()
        if 'context' in input_instance and input_instance['context'] is None:
            del input_instance['context']

        if 'examples' in input_instance and input_instance['examples'] is None:
            del input_instance['examples']

        data = {
            'instances': [
                input_instance,
            ],
            'parameters': {
                'maxOutputTokens': self._config.maxOutputTokens,
                'temperature': self._config.temperature,
                'topK': self._config.topK,
                'topP': self._config.topP,
            },
        }
        with requests.post(api_url, headers=headers, json=data) as response:
            response.raise_for_status()
            response_data = response.json()
            async_to_sync(self._output_stream.write)(
                TextChatOutput(
                    prediction=TextChatPrediction(
                        content=response_data['predictions'][0]['candidates'][0]['content'],
                    ),
                ),
            )

        output = self._output_stream.finalize()
        return output
