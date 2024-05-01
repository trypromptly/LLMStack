import base64
import logging
import os
import shutil
import tempfile
import uuid
from enum import Enum
from io import BytesIO
from typing import Dict, Optional

import grpc
from asgiref.sync import async_to_sync
from django.conf import settings
from pydantic import Field, root_validator

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.acars.proto import runner_pb2, runner_pb2_grpc
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


def _mime_type_from_file_ext(ext):
    if ext == "txt":
        return "text/plain"
    elif ext == "html":
        return "text/html"
    elif ext == "css":
        return "text/css"
    elif ext == "js":
        return "application/javascript"
    elif ext == "json":
        return "application/json"
    elif ext == "xml":
        return "application/xml"
    elif ext == "csv":
        return "text/csv"
    elif ext == "tsv":
        return "text/tab-separated-values"
    elif ext == "md":
        return "text/markdown"
    elif ext == "pdf":
        return "application/pdf"
    else:
        return "application/octet-stream"


def _file_extension_from_mime_type(mime_type):
    if mime_type == "text/plain":
        return "txt"
    elif mime_type == "text/html":
        return "html"
    elif mime_type == "text/css":
        return "css"
    elif mime_type == "application/javascript":
        return "js"
    elif mime_type == "application/json":
        return "json"
    elif mime_type == "application/xml":
        return "xml"
    elif mime_type == "text/csv":
        return "csv"
    elif mime_type == "text/tab-separated-values":
        return "tsv"
    elif mime_type == "text/markdown":
        return "md"
    elif mime_type == "application/pdf":
        return "pdf"
    else:
        return "bin"


def create_data_uri(data, mime_type="text/plain", base64_encode=False, filename=None):
    # Encode data in Base64 if requested
    if base64_encode:
        data = base64.b64encode(data).decode("utf-8")

    # Build the Data URI
    data_uri = f"data:{mime_type}"
    if filename:
        data_uri += f";name={filename}"
    if base64_encode:
        data_uri += ";base64"
    data_uri += f",{data}"

    return data_uri


class FileMimeType(str, Enum):
    TEXT = "text/plain"
    HTML = "text/html"
    CSS = "text/css"
    JAVASCRIPT = "application/javascript"
    JSON = "application/json"
    XML = "application/xml"
    CSV = "text/csv"
    TSV = "text/tab-separated-values"
    MARKDOWN = "text/markdown"
    PDF = "application/pdf"
    OCTET_STREAM = "application/octet-stream"

    def __str__(self):
        return self.value


class FileOperationsInput(ApiProcessorSchema):
    content: str = Field(
        default="",
        description="The contents of the file. Skip this field if you want to create an archive of the directory",
    )
    content_mime_type: Optional[FileMimeType] = Field(
        default=None,
        description="The mimetype of the content.",
    )
    content_objref: Optional[str] = Field(
        default=None,
        description="Object ref of the content to be used to create the file",
    )
    filename: Optional[str] = Field(
        description="The name of the file to create. If not provided, a random name will be generated",
    )
    directory: Optional[str] = Field(
        description="The directory to create the file in. If not provided, the file will be created in a temporary directory and path is returned",
    )
    mimetype: str = Field(
        description="The mimetype of the file. If not provided, it will be inferred from the filename",
    )

    @root_validator
    def validate_input(cls, values):
        mimetype = values.get("mimetype")
        if not mimetype:
            filename = values.get("filename")
            if filename:
                file_extension = filename.split(".")[-1]
                mimetype = _mime_type_from_file_ext(file_extension)
                values["mimetype"] = mimetype
        return values


class FileOperationOperation(str, Enum):
    CREATE = "create"
    ARCHIVE = "archive"
    CONVERT = "convert"


class FileOperationsOutput(ApiProcessorSchema):
    directory: str = Field(description="The directory the file was created in")
    filename: str = Field(description="The name of the file created")
    objref: Optional[str] = Field(default=None, description="Object ref of the file created")


class FileOperationsConfiguration(ApiProcessorSchema):
    operation: FileOperationOperation = Field(description="The operation to perform")
    operation_config: Dict[str, str] = Field(default={}, description="Configuration for the operation")


def _create_archive(files, directory=""):
    """
    Using django storage, recursively copies all the files to a temporary directory and creates an archive
    """
    zip_file_bytes = None
    zip_filedata_uri = None

    # Create a temporary directory to store the files
    with tempfile.TemporaryDirectory() as temp_archive_dir:
        archive_name = f"{temp_archive_dir}.zip".replace("/", "_")

        # Create files in the temporary directory
        for file in files:
            name = file["name"]
            if directory and not name.startswith(directory):
                continue

            if os.path.dirname(name):
                abs_directory_path = os.path.join(temp_archive_dir, os.path.dirname(name))
                if not os.path.exists(abs_directory_path):
                    os.makedirs(abs_directory_path, exist_ok=True)

            data_uri = file["data_uri"]
            mime_type, file_name, b64_file_data = validate_parse_data_uri(data_uri)
            file_data_bytes = base64.b64decode(b64_file_data)

            with open(os.path.join(temp_archive_dir, name), "wb") as f:
                f.write(file_data_bytes)

        # Create an archive of the temporary directory
        shutil.make_archive(temp_archive_dir, "zip", temp_archive_dir)

        # Save the archive to the storage

        with open(f"{temp_archive_dir}.zip", "rb") as f:
            zip_file_bytes = f.read()
            zip_filedata_uri = create_data_uri(
                zip_file_bytes, "application/zip", base64_encode=True, filename=archive_name
            )

    return (zip_filedata_uri, archive_name)


class FileOperationsProcessor(
    ApiProcessorInterface[FileOperationsInput, FileOperationsOutput, FileOperationsConfiguration],
):
    @staticmethod
    def name() -> str:
        return "File Operations"

    @staticmethod
    def slug() -> str:
        return "file_operations"

    @staticmethod
    def description() -> str:
        return "Creates files, directories and archives with provided content"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    @classmethod
    def get_output_template(cls) -> Optional[OutputTemplate]:
        return OutputTemplate(markdown="File: {{objref}}")

    def process(self) -> dict:
        input_content_bytes = None
        input_content_mime_type = None
        data_uri = None

        output_stream = self._output_stream
        directory = self._input.directory or ""
        operation = self._config.operation

        filename = self._input.filename or f"{str(uuid.uuid4())}.{_file_extension_from_mime_type(self._input.mimetype)}"

        if self._input.content:
            input_content_bytes = self._input.content.encode("utf-8")
            input_content_mime_type = self._input.content_mime_type or FileMimeType.TEXT

        if self._input.content_objref:
            # Get the content from the object ref
            file_data_url = self._get_session_asset_data_uri(self._input.content_objref, include_name=True)
            input_content_mime_type, _, input_content_bytes = validate_parse_data_uri(file_data_url)

        full_file_path = f"{directory}/{filename}" if directory else filename

        if operation == FileOperationOperation.CONVERT:
            if input_content_bytes is None or input_content_mime_type is None:
                raise ValueError("Content is missing or invalid")
            with grpc.insecure_channel(f"{settings.RUNNER_HOST}:{settings.RUNNER_PORT}") as channel:
                stub = runner_pb2_grpc.RunnerStub(channel)
                request = runner_pb2.FileConverterRequest(
                    file=runner_pb2.Content(
                        data=input_content_bytes,
                        mime_type=input_content_mime_type,
                    ),
                    target_mime_type=self._input.mimetype,
                    options={},
                )
                response_iter = stub.GetFileConverter(iter([request]))
                response_buffer = BytesIO()
                for response in response_iter:
                    response_buffer.write(response.data)
                response_buffer.seek(0)
                data_uri = create_data_uri(
                    response_buffer.read(), self._input.mimetype, base64_encode=True, filename=full_file_path
                )

        elif operation == FileOperationOperation.CREATE:
            if input_content_bytes is None or input_content_mime_type is None:
                raise ValueError("Content is missing or invalid")
            if input_content_mime_type != self._input.mimetype:
                raise ValueError("Source content mime type does not match provided mime type")

            data_uri = create_data_uri(
                input_content_bytes, input_content_mime_type, base64_encode=True, filename=full_file_path
            )
        elif operation == FileOperationOperation.ARCHIVE:
            result = self._get_all_session_assets(include_name=True, include_data=True)
            if result and "assets" in result and len(result["assets"]):
                zipped_assets, archive_name = _create_archive(result["assets"], directory)
                data_uri = zipped_assets

        if data_uri:
            asset = self._upload_asset_from_url(asset=data_uri)

            async_to_sync(output_stream.write)(
                FileOperationsOutput(directory=directory, filename=filename, objref=asset)
            )
        else:
            raise ValueError("Failed to create data uri")

        # Finalize the output stream
        output = output_stream.finalize()
        return output
