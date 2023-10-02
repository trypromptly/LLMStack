from enum import Enum
from pydantic import Field

from llmstack.apps.types.app_type_interface import AppTypeInterface
from llmstack.apps.types.app_type_interface import BaseSchema


class AgentModel(str, Enum):
    GPT_3_5 = 'gpt-3.5-turbo'
    GPT_3_5_16K = 'gpt-3.6-turbo-16k'
    GPT_4 = 'gpt-4'
    GPT_4_32K = 'gpt-4-32k'

    def __str__(self):
        return self.value


class AgentConfigSchema(BaseSchema):
    model: AgentModel = Field(
        title='Model',
        default=AgentModel.GPT_3_5, description='The model to use for the agent.',
    )
    max_steps: int = Field(
        title='Max Steps',
        default=10, description='The maximum number of steps the agent can take.',
    )
    split_tasks: bool = Field(
        title='Split Tasks',
        default=True, description='Whether to split tasks into subtasks.',
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
