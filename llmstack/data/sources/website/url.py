import logging
from typing import Optional

from pydantic import Field

from llmstack.common.utils.text_extract import ExtraParams, extract_text_from_url
from llmstack.data.sources.base import BaseSource, SourceDataDocument

logger = logging.getLogger(__file__)

"""
Entry configuration schema for url data source type
"""


def get_url_data(url: str, connection=None, **kwargs):
    if not url.startswith("https://") and not url.startswith("http://"):
        url = f"https://{url}"

    text = extract_text_from_url(
        url,
        extra_params=ExtraParams(openai_key=kwargs.get("openai_key"), connection=connection),
    )
    return text


class URLSchema(BaseSource):
    urls: str = Field(
        description="URLs to scrape, List of URL can be comma or newline separated. If site.xml is present, it will be used to scrape the site.",
        max_length=1600,
        json_schema_extra={
            "widget": "webpageurls",
        },
    )
    connection_id: Optional[str] = Field(
        default=None,
        description="Select connection if parsing loggedin page",
        json_schema_extra={"widget": "connection"},
    )

    @classmethod
    def slug(cls):
        return "url"

    @classmethod
    def provider_slug(cls):
        return "promptly"

    def display_name(self):
        return f"{self.urls[0]} and {len(self.urls) - 1} more"

    def get_data_documents(self, **kwargs):
        urls = self.urls.split("\n")
        urls = [url.strip().rstrip() for url_list in [url.split(",") for url in urls] for url in url_list]
        # Filter out empty urls
        urls = list(set(list(filter(lambda url: url != "", urls))))
        # Filter out sitemap.xml
        urls = list(filter(lambda url: not url.endswith(".xml"), urls))
        documents = []
        for url in urls:
            documents.append(SourceDataDocument(name=url, content=url, metadata={"source": url}))
        return documents

    def process_document(self, document: SourceDataDocument) -> SourceDataDocument:
        url_text_data = get_url_data(document.content, connection=self.connection_id)
        return document.model_copy(update={"text": url_text_data, "content": url_text_data.encode()})
