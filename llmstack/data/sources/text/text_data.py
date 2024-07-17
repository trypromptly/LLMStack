import logging

from llmstack.data.sources.base import BaseSource, SourceDataDocument

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
            SourceDataDocument(
                name=self.name,
                content=self.content.encode("utf-8"),
                text=self.content,
                mimetype="text/plain",
                metadata={"source": self.name, "mime_type": "text/plain"},
            )
        ]
