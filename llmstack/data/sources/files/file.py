import logging

from pydantic import Field

from llmstack.common.blocks.data.source import DataSourceEnvironmentSchema
from llmstack.common.blocks.data.source.uri import Uri, UriConfiguration, UriInput
from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.common.utils.splitter import CSVTextSplitter, SpacyTextSplitter
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
                "text/csv": [],
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

    def display_name(self):
        files = self.file.split("|")
        mime_type, file_name, file_data = validate_parse_data_uri(files[0])
        return file_name

    def get_data_documents(self):
        files = self.file.split("|")
        docs = []
        for file in files:
            mime_type, file_name, file_data = validate_parse_data_uri(file)
            data_uri = f"data:{mime_type};name={file_name};base64,{file_data}"
            result = Uri().process(
                input=UriInput(env=DataSourceEnvironmentSchema(openai_key=self.openai_key), uri=data_uri),
                configuration=UriConfiguration(),
            )
            file_text = ""
            for doc in result.documents:
                file_text += doc.content.decode() + "\n"

            if mime_type == "text/csv":
                for document in [
                    Document(page_content_key=self.get_content_key(), page_content=t, metadata={"source": file_name})
                    for t in CSVTextSplitter(
                        chunk_size=2, length_function=CSVTextSplitter.num_tokens_from_string_using_tiktoken
                    ).split_text(file_text)
                ]:
                    docs.append(document)
            else:
                for document in [
                    Document(page_content_key=self.get_content_key(), page_content=t, metadata={"source": file_name})
                    for t in SpacyTextSplitter(chunk_size=1500).split_text(file_text)
                ]:
                    docs.append(document)

        return docs
