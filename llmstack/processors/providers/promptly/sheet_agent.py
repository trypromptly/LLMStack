import ast
import datetime
import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Union

from asgiref.sync import async_to_sync
from pydantic import BaseModel, Field

from llmstack.apps.apis import AppViewSet
from llmstack.apps.schemas import OutputTemplate
from llmstack.common.blocks.base.schema import StrEnum
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.promptly import get_llm_client_from_provider_config
from llmstack.processors.providers.promptly.chat_completions import (
    GoogleModelConfig,
    OpenAIModelConfig,
)

logger = logging.getLogger(__name__)


class TootlType(StrEnum):
    PROMPTLY_PROCESSOR = "promptly_processor"
    PROMPTLY_STORE_APP = "promptly_store_app"


class SheetCellType(StrEnum):
    TEXT = "text"
    JSON_OBJECT = "json_object"
    NUMBER = "number"


class Tool(BaseModel):
    name: str
    description: str
    llm_instruction: str = ""
    schema: Dict[str, Any] = {}
    tool_id: str
    tool_type: TootlType
    tool_provider_slug: str = "promptly"
    tool_slug: str = ""


TOOLS = {
    "web_search": Tool(
        name="Web Search",
        description="Issues a query to a search engine and returns the results",
        schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query to search for",
                }
            },
            "required": ["query"],
        },
        tool_id="web_search",
        tool_type=TootlType.PROMPTLY_PROCESSOR,
        tool_provider_slug="promptly",
        tool_slug="web_search",
    ),
}


class ToolChoice(StrEnum):
    web_search = "web_search"


class SheetAgentInput(ApiProcessorSchema):
    tools: List[str] = Field(
        description="Select the tool to use",
        json_schema_extra={"widget": "select", "options": [f"{tool.name}" for tool in TOOLS.values()]},
    )
    prompt: str = Field(
        description="The instructions for the sheet agent", json_schema_extra={"widget": "textarea"}, default=""
    )
    spread_output: bool = Field(
        description="Whether to spread the output",
        # json_schema_extra={"widget": "hidden"},
        default=True,
    )
    cell_type: SheetCellType = Field(
        description="The type of cell",
        json_schema_extra={
            # "widget": "hidden",
        },
        default=SheetCellType.TEXT,
    )


class SheetAgentConfiguration(ApiProcessorSchema):
    connection_id: Optional[str] = Field(
        default=None,
        json_schema_extra={"widget": "connection"},
        description="Use your authenticated connection to make the request",
    )

    provider_config: Union[
        OpenAIModelConfig,
        GoogleModelConfig,
    ] = Field(default=OpenAIModelConfig(), json_schema_extra={"descrmination_field": "provider"})

    seed: Optional[int] = Field(
        default=None,
        description="The seed used for the agent.",
    )

    temperature: Optional[float] = Field(
        default=0.7,
        description="The temperature of the agent.",
        le=1.0,
        ge=0.0,
    )


class SheetAgentOutput(ApiProcessorSchema):
    output: Union[str, Dict[str, Any]] = Field(
        default="",
        description="Output from the agent",
    )


def run_agent_loop(
    client,
    llm_model_name,
    llm_seed,
    llm_temperature,
    messages,
    llm_tools,
    tool_callback_fn,
    max_invocation_count=5,
):
    # Run first instruction
    first_instruction = True
    tool_calls = []
    llm_invocation_count = 0
    while (first_instruction or len(tool_calls)) and llm_invocation_count < max_invocation_count:
        pending_tool_calls = len(tool_calls)
        while pending_tool_calls:
            tool_call = tool_calls.pop(0)
            tool_call_response = tool_callback_fn(tool_call)
            messages.append(tool_call["assistant_message"])
            messages.append(
                {
                    "role": "tool",
                    "content": json.dumps(tool_call_response),
                    "tool_call_id": tool_call["tool_call_id"],
                }
            )
            pending_tool_calls -= 1

        response = client.chat.completions.create(
            messages=messages,
            tools=llm_tools,
            model=llm_model_name,
            stream=False,
            seed=llm_seed,
            temperature=llm_temperature,
        )
        if first_instruction:
            first_instruction = False
        llm_invocation_count += 1
        choice = response.choices[0]
        if choice.message.tool_calls:
            for tool_call_message in choice.message.tool_calls:
                if tool_call_message.type == "function":
                    tool_calls.append(
                        {
                            "assistant_message": choice.message.model_dump(),
                            "tool_call_id": tool_call_message.id,
                            "arguments": tool_call_message.function.arguments,
                            "tool_name": tool_call_message.function.name,
                        }
                    )

        elif choice.message.content:
            messages.append(
                {
                    "role": "assistant",
                    "content": choice.message.content,
                },
            )

    return messages


class SheetAgentProcessor(
    ApiProcessorInterface[SheetAgentInput, SheetAgentOutput, SheetAgentConfiguration],
):
    """
    Sheet Agent API processor
    """

    @staticmethod
    def name() -> str:
        return "Sheet Agent"

    @staticmethod
    def slug() -> str:
        return "sheet_agent"

    @staticmethod
    def description() -> str:
        return "Sheet Agent Helper"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    @classmethod
    def get_output_template(cls) -> Optional[OutputTemplate]:
        return OutputTemplate(
            markdown="""{{output}}""",
            jsonpath="$.output",
        )

    def execute_tool(self, tool_call: dict) -> dict:
        tool_detail = TOOLS.get(tool_call["tool_name"])
        self._request.data = {
            "stream": False,
            "input": {
                "input": json.loads(tool_call["arguments"]),
                "config": {},
                "api_provider_slug": tool_detail.tool_provider_slug,
                "api_backend_slug": tool_detail.tool_slug,
            },
        }
        response = AppViewSet().run_playground_internal(
            session_id=self._metadata.get("session_id"),
            request_uuid=str(uuid.uuid4()),
            request=self._request,
        )
        try:
            return ast.literal_eval(response.get("output"))
        except Exception:
            return {"error": "Error in executing tool"}

    def process(self) -> dict:
        SYSTEM_MESSAGE = (
            """You are Promptly Sheets Agent a large language model. You perform tasks"""
            + """ based on user instruction. Always follow the following Guidelines\n"""
            + """ 1. Never wrap your response in ```json <CODE_TEXT>```.\n"""
            + """ 2. Never ask user any follow up question."""
        )
        if self._input.spread_output:
            SYSTEM_MESSAGE += f"\nAlways respond to the user with JSON List of list of {self._input.cell_type} e.g [[<RESPONSE1>],[<RESPONSE2>]], this response will be used to fill out a grid of rows and cloumns in a sheet. Priotitize filling out columns first before rows."
        else:
            SYSTEM_MESSAGE += f"\nAlways respond to the user with {self._input.cell_type}"

        SYSTEM_MESSAGE += (
            f"""\n\nCurrent Date: {datetime.datetime.now().strftime('YYYY-MM-DD')}."""
            + """\n You have access to tools to help you perform your task."""
        )

        tools_selected = [tool for tool in TOOLS.values() if tool.name in self._input.tools]

        llm_tools = []
        SYSTEM_MESSAGE += "\n\n# Tools\n"
        for tool in tools_selected:
            llm_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.tool_id,
                        "description": tool.description,
                        "parameters": tool.schema,
                    },
                }
            )
            SYSTEM_MESSAGE += f"\n## {tool.name}\n\n{tool.description}\n\n"
            if tool.llm_instruction:
                SYSTEM_MESSAGE += f"{tool.llm_instruction}\n\n"

        client = get_llm_client_from_provider_config(
            provider=self._config.provider_config.provider,
            model_slug=self._config.provider_config.model.value,
            get_provider_config_fn=self.get_provider_config,
        )
        messages = [{"role": "system", "content": SYSTEM_MESSAGE}]
        messages.append({"role": "user", "content": self._input.prompt})
        messages = run_agent_loop(
            client=client,
            llm_model_name=self._config.provider_config.model.model_name(),
            llm_seed=self._config.seed,
            llm_temperature=self._config.temperature,
            messages=messages,
            llm_tools=llm_tools,
            tool_callback_fn=self.execute_tool,
        )
        final_assistant_message = "Error in processing the request"
        for message in messages[-1:]:
            if message["role"] == "assistant":
                final_assistant_message = message["content"]
                break

        async_to_sync(self._output_stream.write)(SheetAgentOutput(output=final_assistant_message))
        return self._output_stream.finalize()
