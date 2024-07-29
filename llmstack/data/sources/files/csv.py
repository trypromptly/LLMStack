import logging
import uuid

from pydantic import Field

from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.data.schemas import DataDocument
from llmstack.data.sources.files.file import FileSchema
from llmstack.data.sources.utils import create_source_document_asset

logger = logging.getLogger(__name__)


class CSVFileSchema(FileSchema):
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

    def get_data_documents(self, **kwargs):
        file_id = str(uuid.uuid4())
        mime_type, file_name, file_data = validate_parse_data_uri(self.file)
        file_objref = create_source_document_asset(
            self.file, datasource_uuid=kwargs["datasource_uuid"], document_id=file_id
        )
        return [
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
            )
        ]
