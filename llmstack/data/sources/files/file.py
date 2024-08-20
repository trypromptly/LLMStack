import base64
import logging
import uuid
from typing import List

from pydantic import Field

from llmstack.common.blocks.data.source import DataSourceEnvironmentSchema
from llmstack.common.blocks.data.source.uri import Uri, UriConfiguration, UriInput
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.data.sources.base import BaseSource, DataDocument
from llmstack.data.sources.utils import (
    create_source_document_asset,
    get_source_document_asset_by_objref,
)

logger = logging.getLogger(__name__)


class FileSchema(BaseSource):
    file: str = Field(
        description="File to be processed",
        json_schema_extra={
            "advanced_parameter": False,
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
                    },
                    datasource_uuid=kwargs["datasource_uuid"],
                    extra_info={"extra_data": self.get_extra_data()},
                )
            )
        return documents

    @classmethod
    def process_document(cls, document: DataDocument) -> DataDocument:
        data_uri = get_source_document_asset_by_objref(document.content)
        result = Uri().process(
            input=UriInput(env=DataSourceEnvironmentSchema(), uri=data_uri),
            configuration=UriConfiguration(),
        )
        text_content = result.documents[0].content_text
        text_data_uri = (
            f"data:text/plain;name={document.id_}_text.txt;base64,{base64.b64encode(text_content.encode()).decode()}"
        )
        text_file_objref = create_source_document_asset(
            text_data_uri,
            datasource_uuid=document.metadata["datasource_uuid"],
            document_id=str(uuid.uuid4()),
        )
        return document.model_copy(update={"text": text_content, "text_objref": text_file_objref})
