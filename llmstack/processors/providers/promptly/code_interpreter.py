import base64
import logging
from enum import Enum
from typing import Dict, List, Optional

import grpc
from asgiref.sync import async_to_sync
from django.conf import settings
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.acars.proto import runner_pb2, runner_pb2_grpc
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
    code: str = Field(description="The code to run", widget="textarea", default="")
    language: CodeInterpreterLanguage = Field(
        title="Language", description="The language of the code", default=CodeInterpreterLanguage.PYTHON
    )
    local_variables: Optional[str] = Field(
        description="Values for the local variables as a JSON string", widget="hidden", hidden=True
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
        channel = grpc.insecure_channel(f"{settings.RUNNER_HOST}:{settings.RUNNER_PORT}")
        stub = runner_pb2_grpc.RunnerStub(channel)

        request = runner_pb2.CodeRunnerRequest(
            session_id="session_id", source_code=self._input.code, timeout_secs=self._config.timeout
        )
        response_iter = stub.GetCodeRunner(
            iter([request]),
            metadata=(
                ("user_session_creds", "user_session_creds"),
                ("session_id", "session_id"),
            ),
        )
        for response in response_iter:
            if response.stdout:
                stdout_result = self.convert_stdout_to_content(response.stdout)
                async_to_sync(self._output_stream.write)(CodeInterpreterOutput(stdout=stdout_result))
            elif response.stderr:
                async_to_sync(self._output_stream.write)(CodeInterpreterOutput(stderr=response.stderr))

        output = self._output_stream.finalize()
        return output
