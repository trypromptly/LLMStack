import json
import logging
from enum import Enum
from typing import Generator, List, Optional

from asgiref.sync import async_to_sync
from pydantic import BaseModel, Field, confloat, conint

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.blocks.llm.openai import FunctionCall as OpenAIFunctionCall
from llmstack.common.blocks.llm.openai import (
    OpenAIChatCompletionsAPIProcessor,
    OpenAIChatCompletionsAPIProcessorConfiguration,
    OpenAIChatCompletionsAPIProcessorInput,
    OpenAIChatCompletionsAPIProcessorOutput,
)
from llmstack.processors.providers.api_processor_interface import (
    CHAT_WIDGET_NAME,
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class ChatCompletionsModel(str, Enum):
    GPT_4 = "gpt-4"
    GPT_4_O = "gpt-4o"
    GPT_4_32K = "gpt-4-32k"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_3_5 = "gpt-3.5-turbo"
    GPT_3_5_16K = "gpt-3.5-turbo-16k"
    GPT_4_LATEST = "gpt-4-0125-preview"
    GPT_4_1106_PREVIEW = "gpt-4-1106-preview"

    def __str__(self):
        return self.value


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"

    def __str__(self):
        return self.value


class FunctionCallResponse(BaseModel):
    name: Optional[str]
    arguments: Optional[str]


class ChatMessage(BaseModel):
    role: Optional[Role] = Field(
        default=Role.USER,
        description="The role of the message sender. Can be 'user' or 'assistant' or 'system'.",
    )
    content: Optional[str] = Field(
        default="",
        description="The message text.",
        json_schema_extra={"widget": "textarea"},
    )
    name: Optional[str] = Field(
        default="",
        widget="hidden",
        description="The name of the author of this message or the function name.",
    )
    function_call: Optional[FunctionCallResponse] = Field(
        widget="hidden",
        description="The name and arguments of a function that should be called, as generated by the model.",
    )


class FunctionCall(ApiProcessorSchema):
    name: str = Field(
        default="",
        description="The name of the function to be called. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64.",
    )
    description: Optional[str] = Field(
        default=None,
        description="The description of what the function does.",
    )
    parameters: Optional[str] = Field(
        title="Parameters",
        json_schema_extra={"widget": "textarea"},
        default=None,
        description="The parameters the functions accepts, described as a JSON Schema object. See the guide for examples, and the JSON Schema reference for documentation about the format.",
    )


class ChatCompletionsInput(ApiProcessorSchema):
    system_message: Optional[str] = Field(
        default="",
        description="A message from the system, which will be prepended to the chat history.",
        json_schema_extra={"widget": "textarea"},
    )
    chat_history: List[ChatMessage] = Field(
        default=[],
        description="A list of messages, each with a role and message text.",
        widget="hidden",
    )
    messages: List[ChatMessage] = Field(
        default=[
            ChatMessage(role=Role.USER, function_call=None),
        ],
        description="A list of messages, each with a role and message text.",
    )
    functions: Optional[List[FunctionCall]] = Field(
        default=None,
        description="A list of functions the model may generate JSON inputs for .",
    )

    class Config:
        title = "Chat Completions Input"


class ChatCompletionsOutput(ApiProcessorSchema):
    choices: List[ChatMessage] = Field(
        default=[],
        description="Messages",
        widget=CHAT_WIDGET_NAME,
    )


class ChatCompletionsConfiguration(
    OpenAIChatCompletionsAPIProcessorConfiguration,
    ApiProcessorSchema,
):
    model: ChatCompletionsModel = Field(
        default=ChatCompletionsModel.GPT_3_5,
        description="ID of the model to use. Currently, only `gpt-3.5-turbo` and `gpt-4` are supported.",
        json_schema_extra={"advanced_parameter": False},
    )
    max_tokens: Optional[conint(ge=1, le=32000)] = Field(
        1024,
        description="The maximum number of tokens allowed for the generated answer. By default, the number of tokens the model can return will be (4096 - prompt tokens).\n",
        example=1024,
        json_schema_extra={"advanced_parameter": False},
    )
    temperature: Optional[confloat(ge=0.0, le=2.0, multiple_of=0.1)] = Field(
        default=0.7,
        description="What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.\n\nWe generally recommend altering this or `top_p` but not both.\n",
        example=1,
        json_schema_extra={"advanced_parameter": False},
    )
    n: Optional[conint(ge=1, le=128)] = Field(
        1,
        description="How many completions to generate for each prompt.\n\n**Note:** Because this parameter generates many completions, it can quickly consume your token quota. Use carefully and ensure that you have reasonable settings for `max_tokens` and `stop`.\n",
        example=1,
        widget="hidden",
    )
    retain_history: Optional[bool] = Field(
        default=False,
        description="Retain and use the chat history. (Only works in apps)",
        json_schema_extra={"advanced_parameter": False},
    )

    auto_prune_chat_history: Optional[bool] = Field(
        default=False,
        description="Automatically prune chat history. This is only applicable if 'retain_history' is set to 'true'.",
    )

    stream: Optional[bool] = Field(widget="hidden", default=True)
    function_call: Optional[str] = Field(
        default=None,
        description="Controls how the model responds to function calls.",
    )


def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613"):
    import tiktoken

    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model in {
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
    }:
        tokens_per_message = 3
        tokens_per_name = 1
    elif model == "gpt-3.5-turbo-0301":
        # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_message = 4
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif "gpt-3.5-turbo" in model:
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")
    elif "gpt-4" in model:
        return num_tokens_from_messages(messages, model="gpt-4-0613")
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""",
        )
    num_tokens = 0

    for message in messages:
        # If message is a string, it's a system message
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


class ChatCompletions(
    ApiProcessorInterface[ChatCompletionsInput, ChatCompletionsOutput, ChatCompletionsConfiguration],
):
    """
    OpenAI Chat Completions API
    """

    def process_session_data(self, session_data):
        self._chat_history = session_data["chat_history"] if "chat_history" in session_data else []

    @staticmethod
    def name() -> str:
        return "ChatGPT"

    @staticmethod
    def slug() -> str:
        return "chatgpt"

    @staticmethod
    def description() -> str:
        return "Takes a series of messages as input, and return a model-generated message as output"

    @staticmethod
    def provider_slug() -> str:
        return "openai"

    @classmethod
    def get_output_template(cls) -> Optional[OutputTemplate]:
        return OutputTemplate(
            markdown="""{% for choice in choices %}
{{choice.content}}
{% endfor %}""",
        )

    def session_data_to_persist(self) -> dict:
        if self._config.retain_history and self._config.auto_prune_chat_history:
            messages = []
            for message in self._chat_history:
                if isinstance(message, ChatMessage):
                    msg_dict = message.dict()
                    messages.append(
                        {
                            "role": msg_dict["role"],
                            "content": msg_dict["content"],
                        },
                    )
                elif isinstance(message, dict):
                    messages.append(
                        {
                            "role": message["role"],
                            "content": message["content"],
                        },
                    )
                else:
                    raise Exception("Invalid chat history")

            # Prune chat history
            while (num_tokens_from_messages(messages) > self._config.max_tokens) and len(messages) > 1:
                messages.pop(0)

            return {"chat_history": messages}

        return {"chat_history": self._chat_history}

    def process(self) -> dict:
        _env = self._env

        if not self._config.stream:
            raise Exception("Stream must be true for this processor.")

        system_message = self._input.system_message

        if len(self._chat_history) == 0:
            # If we don't have any older chat history in the session, use the
            # chat history from the input
            self._chat_history = self._input.chat_history

        chat_history = self._chat_history if self._config.retain_history else self._input.chat_history

        openai_functions = None
        if self._input.functions is not None:
            openai_functions = []
            for function in self._input.functions:
                openai_functions.append(
                    OpenAIFunctionCall(
                        name=function.name,
                        description=function.description,
                        parameters=(
                            json.loads(
                                function.parameters,
                            )
                            if function.parameters is not None
                            else {}
                        ),
                    ),
                )

        openai_chat_completions_api_processor_input = OpenAIChatCompletionsAPIProcessorInput(
            env=_env,
            system_message=system_message,
            chat_history=chat_history,
            messages=self._input.messages,
            functions=openai_functions,
        )

        result_iter: Generator[OpenAIChatCompletionsAPIProcessorOutput] = OpenAIChatCompletionsAPIProcessor(
            self._config.dict(),
        ).process_iter(openai_chat_completions_api_processor_input.dict())

        for result in result_iter:
            if (
                result.choices[0].role is None
                and result.choices[0].content is None
                and result.choices[0].function_call is None
                and result.choices[0].name is None
            ):
                continue
            async_to_sync(self._output_stream.write)(
                ChatCompletionsOutput(choices=result.choices),
            )

        output = self._output_stream.finalize()

        # Update chat history
        for message in self._input.messages:
            self._chat_history.append(message)
        self._chat_history.append(
            {"role": "assistant", "content": output.choices[0].content},
        )

        return output
