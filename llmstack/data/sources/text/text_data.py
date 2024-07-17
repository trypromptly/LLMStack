import logging

from llmstack.common.blocks.data import DataDocument
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

    def get_data_documents(self, **kwargs):
        return [
            DataDocument(
                name=self.name, content=self.content, content_text=self.content, metadata={"source": self.name}
            )
        ]
