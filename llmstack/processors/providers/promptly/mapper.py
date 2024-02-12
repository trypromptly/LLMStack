import json
import logging
from typing import Any, List, Literal, Optional, Union

import jinja2
from asgiref.sync import async_to_sync
from pydantic import BaseModel, Field

from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class PromptlyApp(BaseModel):
    mapper_type: Literal["promptly_app"] = "promptly_app"
    published_app_id: str


class PythonLambdaFn(BaseModel):
    mapper_type: Literal["python_lambda"] = "python_lambda"
    lambda_expr: str = Field(default="lambda x: x.upper()")


class JinjaMapperFilter(BaseModel):
    mapper_type: Literal["jinja"] = "jinja"
    jinja_expression: str = Field(default="map('upper')")


class MapProcessorInput(ApiProcessorSchema):
    input_list: List[str] = []
    input: Optional[str] = None


class MapProcessorOutput(ApiProcessorSchema):
    output_list: List[Any] = []
    output_str: str = None


class MapProcessorConfiguration(ApiProcessorSchema):
    mapper: Union[JinjaMapperFilter, PythonLambdaFn, PromptlyApp] = Field(
        discriminator="mapper_type", advanced_parameter=False
    )


class MapProcessor(
    ApiProcessorInterface[MapProcessorInput, MapProcessorOutput, MapProcessorConfiguration],
):
    """
    Map processor
    """

    @staticmethod
    def name() -> str:
        return "Map"

    @staticmethod
    def slug() -> str:
        return "map"

    @staticmethod
    def description() -> str:
        return "Applies a mapper function to each item in the input list"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    def process(self) -> dict:
        output_stream = self._output_stream

        mapper = self._config.mapper
        input_list = []
        if self._input.input_list:
            input_list = self._input.input_list
        elif self._input.input:
            if not isinstance(self._input.input, list):
                input_list = [self._input.input]
            input_list = self._input.input

        if isinstance(mapper, PythonLambdaFn):
            output_list = []
            lambda_expr = mapper.lambda_expr
            if not lambda_expr.startswith("lambda"):
                raise ValueError("Invalid lambda expression")

            lambda_fn = eval(lambda_expr)
            output_list = list(map(lambda_fn, input_list))

        elif isinstance(mapper, JinjaMapperFilter):
            env = jinja2.Environment()
            template_str = "{{ input_list|" + mapper.jinja_expression + "|list }}"
            template = env.from_string(template_str)

            output_list = eval(template.render(input_list=input_list))
            output_list = [str(x) for x in output_list]
        elif isinstance(mapper, PromptlyApp):
            import requests

            promptly_token = self._env["promptly_token"]
            url = f"https://www.trypromptly.com/api/apps/{mapper.published_app_id}/run"

            headers = {
                "Authorization": f"Bearer {promptly_token}",
                "Content-Type": "application/json",
            }
            if self._input.input:
                input_list = self._input.input
            else:
                input_list = self._input.input_list
            for item in input_list:
                payload = {"input": item, "stream": False}
                response = requests.post(url, headers=headers, json=payload)
                output_list.append(response.json())

        else:
            raise ValueError("Invalid mapper type")

        async_to_sync(output_stream.write)(
            MapProcessorOutput(output_list=output_list, output_str=json.dumps(output_list))
        )

        output = output_stream.finalize()
        return output
