import base64
import io
import logging
import mimetypes
import re
import tarfile
import uuid
import zipfile
from typing import List

from pydantic import Field

from llmstack.common.utils.text_extract import extract_text_elements
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.data.sources.base import BaseSource, DataDocument
from llmstack.data.sources.utils import (
    create_source_document_asset,
    get_document_data_uri_from_objref,
    get_source_document_asset_by_objref,
)

logger = logging.getLogger(__name__)


def extract_archive_files(mime_type, file_name, file_data):
    extracted_files = []
    if mime_type == "application/zip":
        with zipfile.ZipFile(io.BytesIO(base64.b64decode(file_data))) as archive:
            for file_info in archive.infolist():
                if file_info.is_dir() or file_info.file_size == 0 or file_info.filename.startswith("__MACOSX"):
                    continue
                with archive.open(file_info) as file:
                    file_mime_type = mimetypes.guess_type(file_info.filename)[0]
                    filename = file_info.filename
                    filename = "/".join(filename.split("/")[1:])
                    data_uri = f"data:{file_mime_type};name={filename};base64,{base64.b64encode(file.read()).decode()}"
                    extracted_files.append(data_uri)
    elif mime_type in ["application/x-tar", "application/gzip", "application/x-bzip2"]:
        with tarfile.open(fileobj=io.BytesIO(file_data), mode="r:*") as archive:
            for member in archive.getmembers():
                if member.isfile():
                    file = archive.extractfile(member)
                    file_mime_type = mimetypes.guess_type(member.name)[0]
                    data_uri = (
                        f"data:{file_mime_type};name={member.name};base64,{base64.b64encode(file.read()).decode()}"
                    )
                    extracted_files.append(data_uri)
    else:
        logger.warning(f"Unsupported archive mime type: {mime_type}")
    return extracted_files


class ArchiveFileSchema(BaseSource):
    file: str = Field(
        description="File to be processed",
        json_schema_extra={
            "advanced_parameter": False,
            "widget": "file",
            "maxSize": 25000000,
            "maxFiles": 1,
            "accepts": {
                "application/zip": [],
            },
        },
    )
    split_files: bool = Field(
        default=False,
        description="Split the archive into individual files",
        json_schema_extra={"advanced_parameter": True},
    )
    file_regex: str = Field(
        default=None,
        description="Regex to filter files",
        json_schema_extra={"advanced_parameter": True},
    )

    @classmethod
    def slug(cls):
        return "archive"

    @classmethod
    def provider_slug(cls):
        return "promptly"

    def get_data_documents(self, **kwargs) -> List[DataDocument]:
        archive_file = self.file
        # If objref:// is present, get the data URI from the objref
        if archive_file and archive_file.startswith("objref://"):
            archive_file = get_document_data_uri_from_objref(
                archive_file, datasource_uuid=kwargs["datasource_uuid"], request_user=kwargs["request_user"]
            )

        if self.split_files:
            files = extract_archive_files(*validate_parse_data_uri(archive_file))
        else:
            files = [archive_file]

        documents = []
        for file in files:
            file_id = str(uuid.uuid4())
            mime_type, file_name, file_data = validate_parse_data_uri(file)
            if self.split_files and self.file_regex and not re.match(self.file_regex, file_name):
                continue
            file_objref = create_source_document_asset(
                file, datasource_uuid=kwargs["datasource_uuid"], document_id=file_id
            )
            documents.append(
                DataDocument(
                    id_=file_id,
                    name=file_name,
                    content=file_objref,
                    mimetype=mime_type,
                    metadata={
                        "file_name": file_name,
                        "mime_type": mime_type,
                        "source": file_name,
                        "datasource_uuid": kwargs["datasource_uuid"],
                        "file_regex": self.file_regex,
                    },
                    datasource_uuid=kwargs["datasource_uuid"],
                    extra_info={"extra_data": self.get_extra_data()},
                )
            )
        return documents

    @classmethod
    def process_document(cls, document: DataDocument) -> DataDocument:
        data_uri = get_source_document_asset_by_objref(document.content)
        mime_type, file_name, file_data = validate_parse_data_uri(data_uri)

        if mime_type == "application/zip":
            extracted_files = extract_archive_files(mime_type, file_name, file_data)
            elements = []
            text_content = ""
            for extracted_file in extracted_files:
                mime_type, file_name, extracted_file_data = validate_parse_data_uri(extracted_file)
                if document.metadata.get("file_regex") and not re.match(document.metadata["file_regex"], file_name):
                    continue
                text_content += f"File: {file_name}\n"
                decoded_file_data = base64.b64decode(extracted_file_data)
                elements += extract_text_elements(
                    mime_type=mime_type,
                    data=decoded_file_data,
                    file_name=file_name,
                    extra_params=None,
                )
                text_content += "".join([element.text for element in elements])
            text_content += "\n\n"
        else:
            decoded_file_data = base64.b64decode(file_data)
            elements = extract_text_elements(
                mime_type=mime_type, data=decoded_file_data, file_name=file_name, extra_params=None
            )
            text_content = "".join([element.text for element in elements])

        text_data_uri = (
            f"data:text/plain;name={document.id_}_text.txt;base64,{base64.b64encode(text_content.encode()).decode()}"
        )
        text_file_objref = create_source_document_asset(
            text_data_uri,
            datasource_uuid=document.metadata["datasource_uuid"],
            document_id=str(uuid.uuid4()),
        )
        return document.model_copy(update={"text": text_content, "text_objref": text_file_objref})
