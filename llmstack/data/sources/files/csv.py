import logging

from pydantic import Field

from llmstack.common.blocks.data.source import DataSourceEnvironmentSchema
from llmstack.common.blocks.data.source.uri import Uri, UriConfiguration, UriInput
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.data.sources.base import BaseSource

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
        if mime_type != "text/csv":
            raise ValueError(f"Invalid mime type: {mime_type}, expected: text/csv")

        data_uri = f"data:{mime_type};name={file_name};base64,{file_data}"

        result = Uri().process(
            input=UriInput(
                env=DataSourceEnvironmentSchema(),
                uri=data_uri,
            ),
            configuration=UriConfiguration(),
        )
        result.documents[0].name = file_name
        result.documents[0].metadata["file_name"] = file_name
        result.documents[0].metadata["mime_type"] = mime_type

        return result.documents
