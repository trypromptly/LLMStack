import concurrent.futures
import logging
from typing import List, Literal, Optional, Union

from asgiref.sync import async_to_sync
from pydantic import BaseModel, Field, conint

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.blocks.data.store.vectorstore import Document, DocumentQuery
from llmstack.common.blocks.data.store.vectorstore.chroma import Chroma
from llmstack.common.utils.splitter import SpacyTextSplitter
from llmstack.common.utils.text_extraction_service import (
    GoogleVisionTextExtractionService,
    PromptlyTextExtractionService,
)
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class TextExtractorConfig(BaseModel):
    format_text: bool = Field(default=False)


class PromptlyTextExtractorConfig(TextExtractorConfig):
    provider: Literal["promptly"] = "promptly"


class GoogleTextExtractorConfig(TextExtractorConfig):
    provider: Literal["google"] = "google"


TextExtractorProviderConfigType = Union[PromptlyTextExtractorConfig, GoogleTextExtractorConfig]


class Page(BaseModel):
    number: int
    text: str


class DataUriTextExtractorConfiguration(ApiProcessorSchema):
    text_extractor_provider: TextExtractorProviderConfigType = Field(
        description="The text extractor provider", default=PromptlyTextExtractorConfig()
    )

    document_limit: Optional[conint(ge=0, le=10)] = Field(
        description="The maximum number of documents to return",
        default=1,
    )
    text_chunk_size: Optional[conint(ge=500, le=2000)] = Field(
        description="Chunksize of document",
        default=1500,
    )


class DataUriTextExtractorInput(ApiProcessorSchema):
    file: str = Field(
        default="",
        description="The file to extract text from",
        json_schema_extra={
            "widget": "file",
            "maxSize": 50000000,
            "accepts": {
                "application/pdf": [],
                "application/rtf": [],
                "text/plain": [],
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [],
                "application/msword": [],
                "application/vnd.openxmlformats-officedocument.presentationml.presentation": [],
                "application/vnd.ms-powerpoint": [],
                "image/jpeg": [],
                "image/png": [],
            },
        },
    )
    file_data: Optional[str] = Field(
        default="",
        description="The base64 encoded data of file",
    )
    query: Optional[str] = Field(
        default="",
        description="The query to search the document",
    )


class DataUriTextExtractorOutput(ApiProcessorSchema):
    text: str = Field(
        default="",
        description="The extracted text from the file",
        json_schema_extra={"widget": "textarea"},
    )
    pages: Optional[List[Page]] = Field(
        default=None,
        description="The extracted sections from the file",
    )


class DataUriTextExtract(
    ApiProcessorInterface[DataUriTextExtractorInput, DataUriTextExtractorOutput, DataUriTextExtractorConfiguration],
):
    """
    DataUri Text Extractor processor
    """

    def process_session_data(self, session_data):
        self.file_name = session_data["file_name"] if "file_name" in session_data else ""
        self.mime_type = session_data["mime_type"] if "mime_type" in session_data else ""
        self.data = session_data["data"] if "data" in session_data else ""
        self.extracted_text = session_data["extracted_text"] if "extracted_text" in session_data else ""
        self.storage_index_name = session_data["storage_index_name"] if "storage_index_name" in session_data else ""

    @staticmethod
    def name() -> str:
        return "File Extractor"

    @staticmethod
    def slug() -> str:
        return "data_uri_text_extract"

    @staticmethod
    def description() -> str:
        return "Extract text from file represened as data uri"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    @classmethod
    def get_output_template(cls) -> Optional[OutputTemplate]:
        return OutputTemplate(markdown="""{{text}}""")

    def session_data_to_persist(self) -> dict:
        return {
            "extracted_text": self.extracted_text,
            "storage_index_name": self.storage_index_name,
            "file_name": self.file_name,
            "mime_type": self.mime_type,
            "data": self.data,
        }

    def process(self) -> str:
        query = self._input.query
        file = self._input.file or self._input.file_data

        if file is None:
            raise Exception("No file found in input")

        # Extract from objref if it is one
        file = self._get_session_asset_data_uri(file)
        if self._config.text_extractor_provider.provider == "google":
            provider_config = self.get_provider_config(provider_slug="google")
            text_extractor = GoogleVisionTextExtractionService(
                service_account_json=provider_config.service_account_json
            )
        elif self._config.text_extractor_provider.provider == "promptly":
            text_extractor = PromptlyTextExtractionService()

        if not self.extracted_text:
            result = text_extractor.extract_from_uri(file)
            self.extracted_text = (
                result.formatted_text if self._config.text_extractor_provider.format_text else result.text
            )
            self.pages = list(
                map(
                    lambda x: Page(
                        number=x.page_no,
                        text=x.formatted_text if self._config.text_extractor_provider.format_text else x.text,
                    ),
                    result.pages,
                )
            )
            self.file_name = result.file_name

        if query:
            self.temp_store = Chroma(is_persistent=False)
            index_name = self.temp_store.create_temp_index()
            self.storage_index_name = index_name
            with concurrent.futures.ThreadPoolExecutor() as executor:
                text_chunks = SpacyTextSplitter(
                    separator="\n",
                    pipeline="sentencizer",
                    chunk_size=self._config.text_chunk_size,
                ).split_text(self.extracted_text)
                futures = [
                    executor.submit(
                        self.temp_store.add_text,
                        index_name,
                        Document(
                            page_content_key="content",
                            page_content=text_chunk,
                            metadata={"source": self.file_name},
                        ),
                    )
                    for text_chunk in text_chunks
                ]
                concurrent.futures.wait(futures)
            documents: List[Document] = self.temp_store.hybrid_search(
                self.storage_index_name,
                document_query=DocumentQuery(
                    query=query,
                    limit=self._config.document_limit,
                ),
            )

            async_to_sync(self._output_stream.write)(
                DataUriTextExtractorOutput(
                    text="\n".join(
                        [document.page_content for document in documents],
                    ),
                ),
            )
            output = self._output_stream.finalize()
            return output

        async_to_sync(self._output_stream.write)(
            DataUriTextExtractorOutput(text=self.extracted_text, pages=self.pages),
        )
        output = self._output_stream.finalize()
        return output
