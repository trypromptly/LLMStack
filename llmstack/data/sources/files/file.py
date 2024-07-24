import logging
import uuid
from typing import List

from pydantic import Field

from llmstack.common.blocks.data.source import DataSourceEnvironmentSchema
from llmstack.common.blocks.data.source.uri import Uri, UriConfiguration, UriInput
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.data.schemas import DataDocument
from llmstack.data.sources.base import BaseSource
from llmstack.data.sources.utils import (
    create_source_document_asset,
    get_source_document_asset_by_objref,
)

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

    def get_data_documents(self, **kwargs) -> List[DataDocument]:
        files = self.file.split("|")
        documents = []
        for file in files:
            file_id = str(uuid.uuid4())
            mime_type, file_name, file_data = validate_parse_data_uri(file)
            file_objref = create_source_document_asset(
                file, datasource_uuid=kwargs.get("datasource_uuid", None), document_id=file_id
            )
            documents.append(
                DataDocument(
                    id_=file_id,
                    name=file_name,
                    content=file_objref,
                    mimetype=mime_type,
                    metadata={"file_name": file_name, "mime_type": mime_type, "source": file_name},
                )
            )
        return documents

    def process_document(self, document: DataDocument) -> DataDocument:
        data_uri = get_source_document_asset_by_objref(document.content)
        result = Uri().process(
            input=UriInput(env=DataSourceEnvironmentSchema(), uri=data_uri),
            configuration=UriConfiguration(),
        )
        return document.model_copy(update={"text": result.documents[0].content_text})
