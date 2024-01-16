from enum import Enum
from typing import List, Optional

from pydantic import Field

from llmstack.apps.types.app_type_interface import AppTypeInterface, BaseSchema
from llmstack.processors.providers.api_processor_interface import DataUrl


class AgentModel(str, Enum):
    GPT_3_5_LATEST = 'gpt-3.5-turbo-latest'
    GPT_3_5 = 'gpt-3.5-turbo'
    GPT_3_5_16K = 'gpt-3.5-turbo-16k'
    GPT_4 = 'gpt-4'
    GPT_4_32K = 'gpt-4-32k'
    GPT_4_LATEST = 'gpt-4-turbo-latest'

    def __str__(self):
        return self.value


class RendererType(str, Enum):
    CHAT = 'Chat'
    WEB = 'Web'

    def __str__(self):
        return self.value


class AgentConfigSchema(BaseSchema):
    model: AgentModel = Field(
        title='Model',
        default=AgentModel.GPT_3_5_LATEST,
        description='The model to use for the agent.',
    )
    system_message: str = Field(
        title='System Message',
        default='You are a helpful assistant that uses provided tools to perform actions.',
        description='The system message to use with the Agent.',
        widget='textarea',
    )
    max_steps: int = Field(
        title='Max Steps',
        default=10,
        description='The maximum number of steps the agent can take.',
        advanced_parameter=True,
    )
    split_tasks: bool = Field(
        title='Split Tasks',
        default=True, description='Whether to split tasks into subtasks.',
        advanced_parameter=True,
    )
    renderer_type: RendererType = Field(
        title='Renderer Type',
        default=RendererType.CHAT,
        description='Should the agent be rendered as a chat window or a web form.',
        advanced_parameter=True,
    )
    input_template: str = Field(
        title='Page Content',
        default='',
        description='Content to show at the top of the window',
        widget='richtext',
        advanced_parameter=True,
    )
    welcome_message: str = Field(
        title='Welcome Message',
        default='',
        description='Welcome message from assistant to show when the chat session starts',
        advanced_parameter=True,
    )
    assistant_image: DataUrl = Field(
        title='Assistant Image',
        default='',
        description='Icon to show for the messages from assistant',
        accepts={
            'image/*': []},
        widget='file',
        advanced_parameter=True,
    )
    window_color: str = Field(
        title='Primary Color of Chat Window',
        default='#477195',
        description='Color of the chat window',
        widget='color',
        advanced_parameter=True,
    )
    chat_bubble_text: Optional[str] = Field(
        title='App Bubble Text',
        description='Text to show in the app bubble when embedded in another page. If not provided, it shows chat bubble icon.',
        advanced_parameter=True,
    )
    chat_bubble_style: Optional[str] = Field(
        title='App Bubble Style',
        description='CSS style object to apply to the app bubble when embedded in another page',
        advanced_parameter=True,
        widget='textarea',
    )
    suggested_messages: List[str] = Field(
        title='Suggested messages',
        default=[],
        description='List of upto 3 suggested messages to show to the user',
        advanced_parameter=True,
    )
    chat_history_limit: Optional[int] = Field(
        title='Chat History Limit',
        default=0,
        description='Number of messages to keep in chat history',
        advanced_parameter=True,
        le=1000,
        ge=0,
    )
    seed: Optional[int] = Field(
        title='Random Seed',
        default=None,
        description='Random seed to use for the agent',
        advanced_parameter=True,
    )


class Agent(AppTypeInterface[AgentConfigSchema]):
    @staticmethod
    def slug() -> str:
        return 'agent'

    @staticmethod
    def name() -> str:
        return 'Agent'

    @staticmethod
    def description() -> str:
        return 'Agent that can perform actions based on the input from the user'
