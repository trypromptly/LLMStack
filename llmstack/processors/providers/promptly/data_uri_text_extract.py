import concurrent.futures
import logging
from typing import List, Optional

from asgiref.sync import async_to_sync
from pydantic import Field, conint

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.blocks.data.store.vectorstore import Document, DocumentQuery
from llmstack.common.blocks.data.store.vectorstore.chroma import Chroma
from llmstack.common.utils.splitter import SpacyTextSplitter
from llmstack.common.utils.text_extract import (
    ExtraParams,
    extract_text_from_b64_json,
    extract_text_with_gpt,
)
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class DataUriTextExtractorConfiguration(ApiProcessorSchema):
    document_limit: Optional[conint(ge=0, le=10)] = Field(
        description="The maximum number of documents to return",
        default=1,
        advanced_parameter=True,
    )
    text_chunk_size: Optional[conint(ge=500, le=2000)] = Field(
        description="Chunksize of document",
        default=1500,
        advanced_parameter=True,
    )
    use_gpt: Optional[bool] = Field(
        description="Use GPT to extract text",
        default=False,
    )
    gpt_data_extraction_prompt: Optional[str] = Field(
        description="Prompt to use for GPT data extraction",
        default=None,
    )


class DataUriTextExtractorInput(ApiProcessorSchema):
    file: str = Field(
        default="",
        description="The file to extract text from",
        accepts={
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
        maxSize=50000000,
        widget="file",
    )
    file_data: Optional[str] = Field(
        default="",
        description="The base64 encoded data of file",
        pattern=r"data:(.*);name=(.*);base64,(.*)",
    )
    query: Optional[str] = Field(
        default="",
        description="The query to search the document",
    )


class DataUriTextExtractorOutput(ApiProcessorSchema):
    text: str = Field(
        default="",
        description="The extracted text from the file",
        widget="textarea",
    )


class DataUriTextExtract(
    ApiProcessorInterface[
        DataUriTextExtractorInput,
        DataUriTextExtractorOutput,
        DataUriTextExtractorConfiguration,
    ],
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
        return OutputTemplate(
            markdown="""{{text}}""",
        )

    def session_data_to_persist(self) -> dict:
        return {
            "extracted_text": self.extracted_text,
            "storage_index_name": self.storage_index_name,
            "file_name": self.file_name,
            "mime_type": self.mime_type,
            "data": self.data,
        }

    def process(self) -> str:
        openai_api_key = self._env.get("openai_api_key", None)
        query = self._input.query

        file = self._input.file or None
        if (file is None or file == "") and self._input.file_data:
            file = self._input.file_data

        if file is None:
            raise Exception("No file found in input")

        # Extract from objref if it is one
        file = self._get_session_asset_data_uri(file)

        mime_type, file_name, data = validate_parse_data_uri(file)

        if not self.extracted_text:
            if self._config.use_gpt:
                api_key = self._env["openai_api_key"]
                self.extracted_text = extract_text_with_gpt(
                    api_key=api_key,
                    uri=f"data:{mime_type};base64,{data}",
                    extraction_prompt=self._config.gpt_data_extraction_prompt,
                )
            else:
                self.extracted_text = extract_text_from_b64_json(
                    mime_type=mime_type,
                    base64_encoded_data=data,
                    file_name=file_name,
                    extra_params=ExtraParams(openai_key=openai_api_key),
                )

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
                            metadata={
                                "source": file_name,
                            },
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
            DataUriTextExtractorOutput(text=self.extracted_text),
        )
        output = self._output_stream.finalize()
        return output
