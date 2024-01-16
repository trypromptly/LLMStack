import base64
from enum import Enum
import json
import logging
from typing import Dict, List, Optional
from django.conf import settings
from asgiref.sync import async_to_sync

import grpc
from pydantic import Field

from llmstack.common.runner.proto import runner_pb2, runner_pb2_grpc
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.common.blocks.base.processor import Schema
from google.protobuf.struct_pb2 import Struct, Value
from google.protobuf.json_format import ParseDict
from google.protobuf.json_format import MessageToDict

logger = logging.getLogger(__name__)


class PythonCodeRunnerConfiguration(ApiProcessorSchema):
    timeout: int = Field(
        default=5, description='Timeout in seconds', ge=1, le=30)


class FieldType(str, Enum):
    STRING = 'string'
    NUMBER = 'number'
    INTEGER = 'integer'
    BOOLEAN = 'boolean'

    def __str__(self):
        return self.value


class PythonCodeRunnerInputField(Schema):
    name: str = Field(
        default='', description='Name of the input field')
    type: FieldType = Field(
        default='', description='Type of the input field')
    value: str = Field(
        default='', description='Value of the input field')
    default: str = Field(
        default=None, description='Default value of the input field')


class PythonCodeRunnerInput(ApiProcessorSchema):
    inputs: Optional[List[PythonCodeRunnerInputField]] = Field(
        default=None, description='Inputs to the code')
    code: str = Field(
        description='Python code to execute', widget='textarea')


class PythonCodeRunnerOutput(ApiProcessorSchema):
    stdout: List[str] = Field(
        default=[], description='Standard output')
    stderr: str = Field(
        default='', description='Standard error')
    local_variables: Optional[Dict] = Field(description='Result of the code')
    exit_code: int = Field(
        default=0, description='Exit code of the code')


def get_input_dict(inputs: List[PythonCodeRunnerInputField]) -> dict:
    input_dict = {}
    for input in inputs:
        if input.type == FieldType.STRING:
            input_dict[input.name] = input.value if input.value else input.default if input.default else ''
        elif input.type == FieldType.NUMBER:
            input_dict[input.name] = float(
                input.value if input.value else input.default if input.default else 0)
        elif input.type == FieldType.INTEGER:
            input_dict[input.name] = int(
                input.value if input.value else input.default if input.default else 0)
        elif input.type == FieldType.BOOLEAN:
            input_dict[input.name] = (
                input.value == 'true') if input.value else input.default if input.default else 'false'
    return input_dict


class PythonCodeRunner(ApiProcessorInterface[PythonCodeRunnerInput, PythonCodeRunnerOutput, PythonCodeRunnerConfiguration]):
    """
    Python code runner
    """
    @staticmethod
    def name() -> str:
        return 'Python Code Runner'

    @staticmethod
    def slug() -> str:
        return 'python_code_runner'

    @staticmethod
    def description() -> str:
        return 'Run python code'

    @staticmethod
    def provider_slug() -> str:
        return 'promptly'

    def process(self) -> PythonCodeRunnerOutput:
        output_stream = self._output_stream
        stdout = []
        stderr = ''
        result = ''

        input_data = get_input_dict(self._input.inputs)
        logger.info(f'input_data: {input_data}')

        channel = grpc.insecure_channel(
            f'{settings.RUNNER_HOST}:{settings.RUNNER_PORT}')
        stub = runner_pb2_grpc.RunnerStub(channel)
        request = runner_pb2.RestrictedPythonCodeRunnerRequest(source_code=self._input.code,
                                                               input_data=ParseDict(input_data, Struct()) if (
                                                                   input_data and isinstance(input_data, dict) and len(input_data.keys()) > 0) else None,
                                                               timeout_secs=5)
        response_iterator = stub.GetRestrictedPythonCodeRunner(request)
        for response in response_iterator:
            if response.state == runner_pb2.RemoteBrowserState.TERMINATED:
                async_to_sync(output_stream.write)(PythonCodeRunnerOutput(
                    stdout=list(response.stdout),
                    stderr=str(response.stderr),
                    local_variables=MessageToDict(
                        response.local_variables) if response.local_variables else None,
                    exit_code=0
                ))
                break

        output = output_stream.finalize()

        return output
