from typing import Iterable, List, Union

from openai.types.chat import ChatCompletion as _ChatCompletion
from openai.types.chat.chat_completion import (
    ChatCompletionMessage as _ChatCompletionMessage,
)
from openai.types.chat.chat_completion import Choice as _Choice

from llmstack.common.utils.sls.types.chat.chat_completion_message_param import (
    ContentPartParam,
)


class ChatCompletionMessage(_ChatCompletionMessage):
    content: Union[str, Iterable[ContentPartParam]]


class Choice(_Choice):
    message: ChatCompletionMessage


class ChatCompletion(_ChatCompletion):
    choices: List[_Choice]
