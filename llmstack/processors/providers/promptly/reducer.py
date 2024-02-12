import json
import logging
from functools import reduce
from typing import Any, List, Literal, Optional, Union

import jinja2
from asgiref.sync import async_to_sync
from pydantic import BaseModel, Field

from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class PythonLambdaFn(BaseModel):
    mapper_type: Literal["python_lambda"] = "python_lambda"
    lambda_expr: str = Field(default="lambda x, y: x + ', ' + y")


class JinjaReducerFilter(BaseModel):
    mapper_type: Literal["jinja"] = "jinja"
    jinja_expression: str = Field(default="join(', ')")


class ReduceProcessorInput(ApiProcessorSchema):
    input_list: List[str] = []
    input: Optional[str] = None


class ReduceProcessorOutput(ApiProcessorSchema):
    output: Any
    output_str: str = ""


class ReduceProcessorConfiguration(ApiProcessorSchema):
    reducer: Union[JinjaReducerFilter, PythonLambdaFn] = Field(discriminator="mapper_type")


class ReduceProcessor(
    ApiProcessorInterface[ReduceProcessorInput, ReduceProcessorOutput, ReduceProcessorConfiguration],
):
    """
    Reduce processor
    """

    @staticmethod
    def name() -> str:
        return "Reduce"

    @staticmethod
    def slug() -> str:
        return "reduce"

    @staticmethod
    def description() -> str:
        return "Applies a reducer function to reduce the input list to a single result"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    def process(self) -> dict:
        output_stream = self._output_stream

        reducer = self._config.reducer
        input_list = []
        if self._input.input_list:
            input_list = self._input.input_list
        elif self._input.input:
            input_list = eval(self._input.input)

        if isinstance(reducer, PythonLambdaFn):
            output = None
            lambda_expr = reducer.lambda_expr
            if not lambda_expr.startswith("lambda"):
                raise ValueError("Invalid lambda expression")

            reducer_fn = eval(reducer.lambda_expr)
            output = reduce(reducer_fn, input_list) if input_list else ""

        elif isinstance(reducer, JinjaReducerFilter):
            output = None
            env = jinja2.Environment()
            template_str = "{{ input_list | " + reducer.jinja_expression + " }}"
            template = env.from_string(template_str)
            output = template.render(input_list=input_list)

        async_to_sync(output_stream.write)(ReduceProcessorOutput(output=output, output_str=json.dumps(output)))

        output = output_stream.finalize()
        return output
