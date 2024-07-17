import logging

from pydantic import Field

from llmstack.common.blocks.data.source import DataSourceEnvironmentSchema
from llmstack.common.blocks.data.source.uri import Uri, UriConfiguration, UriInput
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.data.sources.base import BaseSource, SourceDataDocument

logger = logging.getLogger(__name__)


class CSVFileSchema(BaseSource):
    file: str = Field(
        description="File to be processed",
        json_schema_extra={"widget": "file", "accept": {"text/csv": []}, "maxSize": 20000000},
    )

    @classmethod
    def slug(cls):
        return "csv"

    @classmethod
    def provider_slug(cls):
        return "promptly"

    def get_data_documents(self):
        mime_type, file_name, file_data = validate_parse_data_uri(self.file)
        return [
            SourceDataDocument(
                name=file_name,
                content=file_data,
                mimetype=mime_type,
                metadata={"file_name": file_name, "mime_type": mime_type, "source": file_name},
            )
        ]

    def process_document(self, document: SourceDataDocument) -> SourceDataDocument:
        if document.mimetype != "text/csv":
            raise ValueError(f"Invalid mime type: {document.mimetype}, expected: text/csv")
        data_uri = f"data:{document.mimetype};name={document.name};base64,{document.content}"
        result = Uri().process(
            input=UriInput(env=DataSourceEnvironmentSchema(), uri=data_uri),
            configuration=UriConfiguration(),
        )
        return document.model_copy(update={"text": result.documents[0].content_text})
