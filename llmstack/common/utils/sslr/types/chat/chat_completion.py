from typing import List, Union

from openai.types.chat import ChatCompletion as _ChatCompletion
from openai.types.chat.chat_completion import (
    ChatCompletionMessage as _ChatCompletionMessage,
)
from openai.types.chat.chat_completion import Choice as _Choice
from openai.types.chat.chat_completion_message_tool_call import (  # noqa F401
    ChatCompletionMessageToolCall as _ChatCompletionMessageToolCall,
)
from openai.types.chat.chat_completion_message_tool_call import (  # noqa F401
    Function as _Function,
)

from llmstack.common.utils.sslr.types.chat.chat_completion_message_param import (
    ContentPartParam,
)


class ChatCompletionMessage(_ChatCompletionMessage):
    content: Union[str, List[ContentPartParam]]

    @property
    def content_str(self):
        content_str = ""
        if isinstance(self.content, str):
            content_str = self.content

        elif isinstance(self.content, list):
            for part in self.content:
                if part["type"] == "text":
                    content_str += part["data"] if "data" in part else part["text"]
                elif part["type"] == "blob":
                    content_str += f"data:{part['mime_type']};base64,{part['data']}"
                elif part["type"] == "file":
                    content_str += f"{part['data']}"

        return content_str

    @property
    def content_parts(self):
        if isinstance(self.content, list):
            return self.content
        return None


class Choice(_Choice):
    message: ChatCompletionMessage


class ChatCompletion(_ChatCompletion):
    choices: List[Choice]
