from typing import List, Optional, Union

from openai.types.chat import ChatCompletionChunk as _ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice as _Choice
from openai.types.chat.chat_completion_chunk import ChoiceDelta as _ChoiceDelta
from openai.types.chat.chat_completion_chunk import (
    ChoiceDeltaToolCall as _ChoiceDeltaToolCall,
)
from openai.types.chat.chat_completion_chunk import (
    ChoiceDeltaToolCallFunction as _ChoiceDeltaToolCallFunction,
)
from pydantic import root_validator

from llmstack.common.utils.sls.types.chat.chat_completion_message_param import (
    ContentPartParam,
)


class ChoiceDelta(_ChoiceDelta):
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
                        _ChoiceDeltaToolCall(
                            type="function",
                            function=_ChoiceDeltaToolCallFunction(name=part["tool_name"], arguments=part["tool_args"]),
                        )
                    )

            values["content_str"] = content_str
            if tool_calls:
                values["tool_calls"] = tool_calls

        return values


class Choice(_Choice):
    delta: ChoiceDelta


class ChatCompletionChunk(_ChatCompletionChunk):
    choices: List[Choice]
