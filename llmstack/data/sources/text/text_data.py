import base64
import logging
import uuid

from llmstack.data.schemas import DataDocument
from llmstack.data.sources.base import BaseSource
from llmstack.data.sources.utils import create_source_document_asset

logger = logging.getLogger(__file__)

"""
Entry configuration schema for text data source type
"""


class TextSchema(BaseSource):
    name: str = "Untitled"
    content: str = ""

    @classmethod
    def slug(cls):
        return "text"

    @classmethod
    def provider_slug(cls):
        return "promptly"

    def get_data_documents(self, **kwargs):
        id = str(uuid.uuid4())
        data_uri = f"data:text/plain;name={self.name}.txt;base64,{base64.b64encode(self.content.encode('utf-8')).decode('utf-8')}"
        file_objref = create_source_document_asset(
            data_uri, datasource_uuid=kwargs.get("datasource_uuid", None), document_id=id
        )

        return [
            DataDocument(
                id_=id,
                name=self.name,
                content=file_objref,
                text=self.content,
                mimetype="text/plain",
                metadata={"source": self.name, "mime_type": "text/plain"},
                datasource_uuid=kwargs["datasource_uuid"],
            )
        ]
