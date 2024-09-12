import base64
import logging
import uuid
from typing import Dict, List, Optional

import grpc
from asgiref.sync import async_to_sync
from django.conf import settings
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.blocks.base.schema import StrEnum
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.promptly import Content, ContentMimeType

logger = logging.getLogger(__name__)


class CodeInterpreterLanguage(StrEnum):
    PYTHON = "Python"


class CodeInterpreterInput(ApiProcessorSchema):
    code: str = Field(description="The code to run", json_schema_extra={"widget": "textarea"}, default="")
    language: CodeInterpreterLanguage = Field(
        title="Language", description="The language of the code", default=CodeInterpreterLanguage.PYTHON
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

{% endfor %}""",
            jsonpath="$.stdout",
        )

    def convert_stdout_to_content(self, stdout) -> List[Content]:
        from langrocks.common.models import runner_pb2

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

    def process_session_data(self, session_data):
        self._kernel_session_id = session_data.get("kernel_session_id", None)

    def session_data_to_persist(self) -> dict:
        return {
            "kernel_session_id": self._kernel_session_id,
        }

    def process(self) -> dict:
        from langrocks.common.models import runner_pb2, runner_pb2_grpc

        kernel_session_id = self._kernel_session_id if self._kernel_session_id else str(uuid.uuid4())

        channel = grpc.insecure_channel(f"{settings.RUNNER_HOST}:{settings.RUNNER_PORT}")
        stub = runner_pb2_grpc.RunnerStub(channel)

        request = runner_pb2.CodeRunnerRequest(source_code=self._input.code, timeout_secs=self._config.timeout)
        response_iter = stub.GetCodeRunner(
            iter([request]),
            metadata=(("kernel_session_id", kernel_session_id),),
        )
        for response in response_iter:
            if response.stdout:
                stdout_result = self.convert_stdout_to_content(response.stdout)
                async_to_sync(self._output_stream.write)(CodeInterpreterOutput(stdout=stdout_result))

            if response.stderr:
                async_to_sync(self._output_stream.write)(CodeInterpreterOutput(stderr=response.stderr))

        output = self._output_stream.finalize()
        return output
