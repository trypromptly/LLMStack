import logging

from pydantic import Field

from llmstack.common.blocks.data.source import DataSourceEnvironmentSchema
from llmstack.common.blocks.data.source.uri import Uri, UriConfiguration, UriInput
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.data.sources.base import BaseSource, SourceDataDocument

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
        documents = []
        for file in files:
            mime_type, file_name, file_data = validate_parse_data_uri(file)
            documents.append(
                SourceDataDocument(
                    name=file_name,
                    content=file_data,
                    mimetype=mime_type,
                    metadata={"file_name": file_name, "mime_type": mime_type, "source": file_name},
                )
            )
        return documents

    def process_document(self, document: SourceDataDocument) -> SourceDataDocument:
        data_uri = f"data:{document.mimetype};name={document.name};base64,{document.content}"
        result = Uri().process(
            input=UriInput(env=DataSourceEnvironmentSchema(), uri=data_uri),
            configuration=UriConfiguration(),
        )
        return document.model_copy(update={"text": result.documents[0].content_text})
