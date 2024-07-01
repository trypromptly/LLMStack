import logging

from pydantic import BaseModel, Field

from llmstack.processors.providers.api_processor_interface import (
    TEXT_WIDGET_NAME,
    ApiProcessorInterface,
)

logger = logging.getLogger(__name__)


class CompletionsConfiguration(BaseModel):
    model: str = Field(
        default="",
        description="The model to use for completion.",
    )

    class Config:
        title = "CompletionsConfiguration"


class CompletionsInput(BaseModel):
    prompt: str = Field(default="", description="The prompt to complete.")

    class Config:
        title = "CompletionsInput"


class CompletionsOutput(BaseModel):
    result: str = Field(default="", json_schema_extra={"widget": TEXT_WIDGET_NAME})


class Completions(
    ApiProcessorInterface[CompletionsInput, CompletionsOutput, CompletionsConfiguration],
):
    """
    Forefront Completions
    """

    def __init__(self, configuration, session_data):
        super().__init__(configuration, session_data)

    def name() -> str:
        return "forefront ai/completions"

    def process(self, input: dict) -> dict:
        raise Exception("Not implemented")
