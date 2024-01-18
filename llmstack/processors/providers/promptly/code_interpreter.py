import base64
import logging
from enum import Enum
from typing import Dict, List, Optional

import grpc
import orjson as json
from asgiref.sync import async_to_sync
from django.conf import settings
from google.protobuf.json_format import MessageToDict, ParseDict
from google.protobuf.struct_pb2 import Struct
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.runner.proto import runner_pb2, runner_pb2_grpc
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.promptly import Content, ContentMimeType

logger = logging.getLogger(__name__)


class CodeInterpreterLanguage(str, Enum):
    PYTHON = "Python"

    def __str__(self):
        return self.value


class CodeInterpreterInput(ApiProcessorSchema):
    code: str = Field(description="The code to run", widget="textarea")
    language: CodeInterpreterLanguage = Field(
        title="Language", description="The language of the code", default=CodeInterpreterLanguage.PYTHON
    )
    local_variables: Optional[str] = Field(
        description="Values for the local variables as a JSON string", widget="textarea"
    )


class CodeInterpreterOutput(ApiProcessorSchema):
    stdout: List[Content] = Field(default=[], description="Standard output as a list of Content objects")
    stderr: str = Field(default="", description="Standard error")
    local_variables: Optional[Dict] = Field(description="Local variables as a JSON object")
    exit_code: int = Field(default=0, description="Exit code of the process")


class CodeInterpreterConfiguration(ApiProcessorSchema):
    timeout: int = Field(default=5, description="Timeout in seconds", ge=1, le=30)


class CodeInterpreterProcessor(
    ApiProcessorInterface[CodeInterpreterInput, CodeInterpreterOutput, CodeInterpreterConfiguration],
):
    @staticmethod
    def name() -> str:
        return "Code Interpreter"

    @staticmethod
    def slug() -> str:
        return "code_interpreter"

    @staticmethod
    def description() -> str:
        return "Runs the provided code and returns the output"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    @staticmethod
    def get_output_template() -> Optional[OutputTemplate]:
        return OutputTemplate(
            markdown="""{% for line in stdout %}

{% if line.mime_type == "text/plain" %}
{{ line.data }}
{% endif %}

{% if line.mime_type == "image/png" %}
![Image](data:image/png;base64,{{line.data}})
{% endif %}

{% endfor %}"""
        )

    def convert_stdout_to_content(self, stdout) -> List[Content]:
        content = []
        for entry in stdout:
            if not entry.mime_type or entry.mime_type == runner_pb2.ContentMimeType.TEXT:
                content.append(Content(mime_type=ContentMimeType.TEXT, data=entry.data.decode("utf-8")))
            elif entry.mime_type == runner_pb2.ContentMimeType.JSON:
                content.append(Content(mime_type=ContentMimeType.JSON, data=entry.data.decode("utf-8")))
            elif entry.mime_type == runner_pb2.ContentMimeType.HTML:
                content.append(Content(mime_type=ContentMimeType.HTML, data=entry.data.decode("utf-8")))
            elif entry.mime_type == runner_pb2.ContentMimeType.PNG:
                data = base64.b64encode(entry.data).decode("utf-8")
                content.append(Content(mime_type=ContentMimeType.PNG, data=data))
            elif entry.mime_type == runner_pb2.ContentMimeType.JPEG:
                data = base64.b64encode(entry.data).decode("utf-8")
                content.append(Content(mime_type=ContentMimeType.JPEG, data=data))
            elif entry.mime_type == runner_pb2.ContentMimeType.SVG:
                data = base64.b64encode(entry.data).decode("utf-8")
                content.append(Content(mime_type=ContentMimeType.SVG, data=data))
            elif entry.mime_type == runner_pb2.ContentMimeType.PDF:
                data = base64.b64encode(entry.data).decode("utf-8")
                content.append(Content(mime_type=ContentMimeType.PDF, data=data))
            elif entry.mime_type == runner_pb2.ContentMimeType.LATEX:
                data = base64.b64encode(entry.data).decode("utf-8")
                content.append(Content(mime_type=ContentMimeType.LATEX, data=data))
        return content

    def process(self) -> dict:
        output_stream = self._output_stream
        channel = grpc.insecure_channel(f"{settings.RUNNER_HOST}:{settings.RUNNER_PORT}")
        stub = runner_pb2_grpc.RunnerStub(channel)
        input_data = {}
        if self._input.local_variables:
            try:
                input_data = json.loads(self._input.local_variables)
            except Exception as e:
                logger.error(f"Error parsing local variables: {e}")

        request = runner_pb2.RestrictedPythonCodeRunnerRequest(
            source_code=self._input.code,
            input_data=ParseDict(input_data, Struct()),
            timeout_secs=5,
        )
        response_iterator = stub.GetRestrictedPythonCodeRunner(request)
        for response in response_iterator:
            if response.state == runner_pb2.RemoteBrowserState.TERMINATED:
                converted_stdout = self.convert_stdout_to_content(response.stdout)
                async_to_sync(output_stream.write)(
                    CodeInterpreterOutput(
                        stdout=converted_stdout,
                        stderr=str(response.stderr),
                        local_variables=MessageToDict(response.local_variables) if response.local_variables else None,
                        exit_code=0,
                    )
                )
                break

        output = output_stream.finalize()

        return output
