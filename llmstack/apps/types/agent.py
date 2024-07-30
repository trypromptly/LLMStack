from enum import Enum
from typing import List, Optional

from pydantic import Field

from llmstack.apps.types.app_type_interface import AppTypeInterface, BaseSchema


class AgentModel(str, Enum):
    GPT_3_5_LATEST = "gpt-3.5-turbo-latest"
    GPT_3_5 = "gpt-3.5-turbo"
    GPT_3_5_16K = "gpt-3.5-turbo-16k"
    GPT_4 = "gpt-4"
    GPT_4_32K = "gpt-4-32k"
    GPT_4_LATEST = "gpt-4-turbo-latest"
    GPT_4_1106_PREVIEW = "gpt-4-1106-preview"
    GPT_4_O = "gpt-4o"
    GPT_4_O_MINI = "gpt-4o-mini"

    def __str__(self):
        return self.value


class AgentConfigSchema(BaseSchema):
    model: AgentModel = Field(
        title="Model",
        default=AgentModel.GPT_4_O_MINI,
        description="The model to use for the agent.",
        json_schema_extra={"widget": "customselect"},
    )
    stream: Optional[bool] = Field(
        default=None,
        title="Stream",
        description="Stream the output from the agent",
        json_schema_extra={"advanced_parameter": True},
    )
    user_message: Optional[str] = Field(
        default=None,
        title="User Message",
        description="The user message to use with the Agent. This is the message that the user provides to the agent in the input.",
        json_schema_extra={"widget": "textwithvars"},
    )
    system_message: str = Field(
        title="System Message",
        default="You are a helpful assistant that uses provided tools to perform actions.",
        description="The system message to use with the Agent.",
        json_schema_extra={"widget": "textarea"},
    )
    max_steps: int = Field(
        title="Max Steps",
        default=10,
        description="The maximum number of steps the agent can take.",
        json_schema_extra={"advanced_parameter": True},
        le=100,
        ge=1,
    )
    split_tasks: bool = Field(
        title="Split Tasks",
        default=True,
        description="Whether to split tasks into subtasks.",
        json_schema_extra={"advanced_parameter": True},
    )
    input_template: str = Field(
        title="Page Content",
        default="",
        description="Content to show at the top of the window",
        json_schema_extra={"widget": "richtext", "advanced_parameter": True},
    )
    welcome_message: str = Field(
        title="Welcome Message",
        default="",
        description="Welcome message from assistant to show when the chat session starts",
        json_schema_extra={"advanced_parameter": True},
    )
    assistant_image: str = Field(
        title="Assistant Image",
        default="",
        description="Icon to show for the messages from assistant",
        json_schema_extra={"widget": "hidden", "advanced_parameter": True, "hidden": True},
    )
    window_color: str = Field(
        title="Primary Color of Chat Window",
        default="#477195",
        description="Color of the chat window",
        json_schema_extra={"widget": "color", "advanced_parameter": True},
    )
    chat_bubble_text: Optional[str] = Field(
        default=None,
        title="App Bubble Text",
        description="Text to show in the app bubble when embedded in another page. If not provided, it shows chat bubble icon.",
        json_schema_extra={"advanced_parameter": True},
    )
    chat_bubble_style: Optional[str] = Field(
        default=None,
        title="App Bubble Style",
        description="CSS style object to apply to the app bubble when embedded in another page",
        json_schema_extra={"widget": "textarea", "advanced_parameter": True},
    )
    suggested_messages: List[str] = Field(
        title="Suggested messages",
        default=[],
        description="List of upto 3 suggested messages to show to the user",
        json_schema_extra={"advanced_parameter": True},
    )
    chat_history_limit: Optional[int] = Field(
        title="Chat History Limit",
        default=0,
        description="Number of messages to keep in chat history",
        json_schema_extra={"advanced_parameter": True},
        le=1000,
        ge=0,
    )
    seed: Optional[int] = Field(
        title="Random Seed",
        default=None,
        description="Random seed to use for the agent",
        json_schema_extra={"advanced_parameter": True},
    )
    temperature: Optional[float] = Field(
        title="Temperature",
        default=0.7,
        description="Temperature to use for the agent",
        json_schema_extra={"advanced_parameter": True},
        ge=0.0,
        le=1.0,
    )
    layout: Optional[str] = Field(
        default=None,
        title="Layout",
        description="Layout to use for the app page",
        json_schema_extra={"widget": "textarea", "advanced_parameter": True},
    )
    init_on_load: Optional[bool] = Field(
        default=None,
        title="Initialize processors on load. Use this for apps like realtime avatars.",
        description="If checked, the app will be initialized when the page is loaded. This is useful for apps that need to be initialized before the user interacts with them.",
        json_schema_extra={"advanced_parameter": True, "hidden": True},
    )


class Agent(AppTypeInterface[AgentConfigSchema]):
    @staticmethod
    def slug() -> str:
        return "agent"

    @staticmethod
    def name() -> str:
        return "Agent"

    @staticmethod
    def description() -> str:
        return "Agent that can perform actions based on the input from the user"
