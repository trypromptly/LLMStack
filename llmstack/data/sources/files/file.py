import logging

from pydantic import Field

from llmstack.common.blocks.data.source import DataSourceEnvironmentSchema
from llmstack.common.blocks.data.source.uri import Uri, UriConfiguration, UriInput
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.data.sources.base import BaseSource

logger = logging.getLogger(__name__)


class FileSchema(BaseSource):
    file: str = Field(
        description="File to be processed",
        json_schema_extra={
            "widget": "file",
            "maxSize": 25000000,
            "maxFiles": 4,
            "accepts": {
                "application/pdf": [],
                "application/json": [],
                "audio/mpeg": [],
                "application/rtf": [],
                "text/plain": [],
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [],
                "application/vnd.openxmlformats-officedocument.presentationml.presentation": [],
                "audio/mp3": [],
                "video/mp4": [],
                "video/webm": [],
            },
        },
    )

    @classmethod
    def slug(cls):
        return "file"

    @classmethod
    def provider_slug(cls):
        return "promptly"

    def get_data_documents(self):
        files = self.file.split("|")
        docs = []
        for file in files:
            mime_type, file_name, file_data = validate_parse_data_uri(file)
            data_uri = f"data:{mime_type};name={file_name};base64,{file_data}"
            result = Uri().process(
                input=UriInput(env=DataSourceEnvironmentSchema(), uri=data_uri),
                configuration=UriConfiguration(),
            )
            for doc in result.documents:
                doc.name = file_name
                doc.metadata = {**doc.metadata, "file_name": file_name, "mime_type": mime_type}
                docs.append(doc)
        return docs
