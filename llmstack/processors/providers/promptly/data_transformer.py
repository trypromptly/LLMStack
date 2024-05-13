import json
from typing import Dict, List

from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)


class DataTransformerInput(ApiProcessorSchema):
    input_str: str = Field(description="The input string to transform", widget="textarea", default="{}")


class DataTransformerOutput(ApiProcessorSchema):
    output: List[Dict] = Field(description="The transformed data", widget="textarea", default=[])
    output_str: str = Field(description="The transformed string", widget="textarea", default="[]")


class DataTransformerConfiguration(ApiProcessorSchema):
    pass


class DataTransformerProcessor(
    ApiProcessorInterface[DataTransformerInput, DataTransformerOutput, DataTransformerConfiguration]
):
    @staticmethod
    def name() -> str:
        return "Data Transformer"

    @staticmethod
    def slug() -> str:
        return "data_transformer"

    @staticmethod
    def description() -> str:
        return "Transform Data"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    @classmethod
    def get_output_template(cls) -> OutputTemplate | None:
        return OutputTemplate(
            markdown="{{output_str}}",
        )

    def process(self) -> dict:
        output_stream = self._output_stream
        import ast

        output = []

        try:
            output = ast.literal_eval(self._input.input_str)
        except Exception:
            pass

        async_to_sync(output_stream.write)(DataTransformerOutput(output=output, output_str=json.dumps(output)))

        output = output_stream.finalize()
        return output
