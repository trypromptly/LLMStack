import ast
import json
import logging
import re
from typing import Any, Dict, List, Optional, Union

from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.blocks.base.processor import Schema
from llmstack.common.utils.utils import get_input_model_from_fields
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
    hydrate_input,
)

logger = logging.getLogger(__name__)

data_transformer_template_item_var_regex = re.compile(r"\{\{_data_transformer\.?.*\}\}")


class DataTransformerInput(ApiProcessorSchema):
    input_str: Optional[str] = Field(description="The input string to transform", default="[]")


class DataTransformerOutput(ApiProcessorSchema):
    output: Union[List[Dict[str, Any]], Dict[str, Any]] = Field(description="The transformed data", default=[])
    output_str: str = Field(description="The transformed string", widget="textarea", default="[]")


class FieldType(Schema):
    name: str = Field(title="Field name")
    value: str = Field(title="Field value")


class DataTransformerConfiguration(ApiProcessorSchema):
    fields: List[FieldType] = Field(
        title="Fields", description="Fields in transformed data", default=[], advanced_parameter=False
    )
    transform_input_list: bool = Field(
        title="Is list", description="Is the transformed data input a list", default=True, advanced_parameter=False
    )


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

    def input(self, message: Any) -> Any:
        self.config_data_transformer_fields = {}

        if self._config.transform_input_list:
            # Preserve fields with _data_transformer template item var
            for idx in range(len(self._config.fields)):
                field = self._config.fields[idx]
                if re.match(data_transformer_template_item_var_regex, field.value):
                    self.config_data_transformer_fields[idx] = field

        return super().input(message)

    def process(self) -> dict:
        output_stream = self._output_stream
        config_fields = []

        for idx in range(len(self._config.fields)):
            if idx in self.config_data_transformer_fields:
                config_fields.append(self.config_data_transformer_fields[idx])
            else:
                config_fields.append(self._config.fields[idx])

        output_model_cls = get_input_model_from_fields(
            "DataTransformerOutput",
            list(map(lambda entry: {"type": "string", "name": entry.name, "default": entry.value}, config_fields)),
        )

        if self._config.transform_input_list:
            output_result = []
            _input = ast.literal_eval(self._input.input_str)
            for item in _input:
                output_result.append(hydrate_input(output_model_cls().dict(), {"_data_transformer": item}))
        else:
            output_result = output_model_cls().dict()

        async_to_sync(output_stream.write)(
            DataTransformerOutput(output=output_result, output_str=json.dumps(output_result))
        )

        output = output_stream.finalize()
        return output
