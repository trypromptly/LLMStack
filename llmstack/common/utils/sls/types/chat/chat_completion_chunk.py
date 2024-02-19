from typing import List, Union

from openai.types.chat import ChatCompletionChunk as _ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice as _Choice
from openai.types.chat.chat_completion_chunk import ChoiceDelta as _ChoiceDelta
from openai.types.chat.chat_completion_chunk import (
    ChoiceDeltaToolCall as _ChoiceDeltaToolCall,
)
from openai.types.chat.chat_completion_chunk import (
    ChoiceDeltaToolCallFunction as _ChoiceDeltaToolCallFunction,
)

from llmstack.common.utils.sls.types.chat.chat_completion_message_param import (
    ContentPartParam,
)


class ChoiceDelta(_ChoiceDelta):
    content: Union[str, List[ContentPartParam]]

    @property
    def content_str(self):
        content_str = ""
        if isinstance(self.content, str):
            content_str = self.content

        elif isinstance(self.content, list):
            for part in self.content:
                if part["type"] == "text":
                    content_str += part["data"]
                elif part["type"] == "blob":
                    content_str += f"data:{part['mime_type']};base64,{part['data']}"
                elif part["type"] == "file":
                    content_str += f"{part['data']}"

        return content_str

    @property
    def tool_calls_list(self):
        tool_calls = []
        if isinstance(self.content, list):
            for part in self.content:
                if part["type"] == "tool_call":
                    tool_calls.append(
                        _ChoiceDeltaToolCall(
                            type="function",
                            function=_ChoiceDeltaToolCallFunction(name=part["tool_name"], arguments=part["tool_args"]),
                        )
                    )
        return self.tool_calls or tool_calls

    @property
    def content_parts(self):
        if isinstance(self.content, list):
            return self.content
        return None


class Choice(_Choice):
    delta: ChoiceDelta


class ChatCompletionChunk(_ChatCompletionChunk):
    choices: List[Choice]
