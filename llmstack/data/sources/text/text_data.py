import logging

from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.common.utils.splitter import SpacyTextSplitter
from llmstack.data.sources.base import BaseSource

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

    def display_name(self):
        return f"{self.name}"

    def get_data_documents(self, **kwargs):
        docs = [
            Document(page_content_key="content", page_content=t, metadata={"source": self.name})
            for t in SpacyTextSplitter(chunk_size=1500).split_text(self.content)
        ]

        return docs
