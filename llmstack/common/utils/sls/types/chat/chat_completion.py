from typing import List, Optional, Union

from openai.types.chat import ChatCompletion as _ChatCompletion
from openai.types.chat.chat_completion import (
    ChatCompletionMessage as _ChatCompletionMessage,
)
from openai.types.chat.chat_completion import Choice as _Choice
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall as _ChatCompletionMessageToolCall,
)
from openai.types.chat.chat_completion_message_tool_call import Function as _Function
from pydantic import root_validator

from llmstack.common.utils.sls.types.chat.chat_completion_message_param import (
    ContentPartParam,
)


class ChatCompletionMessage(_ChatCompletionMessage):
    content: Union[str, List[ContentPartParam]]
    content_str: Optional[str]

    @root_validator
    def validate_content_str(cls, values):
        if "content" in values and isinstance(values["content"], str):
            values["content_str"] = values["content"]
        elif "content" in values and isinstance(values["content"], list):
            content_str = ""
            tool_calls = []
            values["content_str"] = ""
            for part in values["content"]:
                if part["type"] == "text":
                    content_str += part["data"]
                elif part["type"] == "blob":
                    content_str += f"data:{part['mime_type']};base64,{part['data']}"
                elif part["type"] == "file":
                    content_str += f"{part['data']}"
                elif part["type"] == "tool_call":
                    tool_calls.append(
                        _ChatCompletionMessageToolCall(
                            type="function", function=_Function(name=part["tool_name"], arguments=part["tool_args"])
                        )
                    )

            values["content_str"] = content_str
            if tool_calls:
                values["tool_calls"] = tool_calls

        return values


class Choice(_Choice):
    message: ChatCompletionMessage


class ChatCompletion(_ChatCompletion):
    choices: List[_Choice]
