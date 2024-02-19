from typing import Iterable, List, Union

from openai.types.chat import ChatCompletionChunk as _ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice as _Choice
from openai.types.chat.chat_completion_chunk import ChoiceDelta as _ChoiceDelta

from llmstack.common.utils.sls.types.chat.chat_completion_message_param import (
    ContentPartParam,
)


class ChoiceDelta(_ChoiceDelta):
    content: Union[str, Iterable[ContentPartParam]]


class Choice(_Choice):
    delta: ChoiceDelta


class ChatCompletionChunk(_ChatCompletionChunk):
    choices: List[Choice]
