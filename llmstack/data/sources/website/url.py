import base64
import json
import logging
import uuid
from enum import Enum
from typing import Optional

from playwright.sync_api import sync_playwright
from pydantic import Field
from unstructured.partition.auto import partition_html

from llmstack.common.utils.text_extract import ExtraParams, extract_text_from_url
from llmstack.data.schemas import DataDocument
from llmstack.data.sources.base import BaseSource
from llmstack.data.sources.utils import create_source_document_asset

logger = logging.getLogger(__file__)


def get_connection_context(connection_id: str, datasource_uuid: str):
    from llmstack.data.models import DataSource

    if not connection_id:
        return None

    datasource = DataSource.objects.filter(uuid=datasource_uuid).first()
    if datasource:
        connection = datasource.profile.get_connection(connection_id)
        if connection and connection.get("connection_type_slug") == "web_login":
            return json.loads(connection.get("configuration", {}).get("_storage_state", "{}"))
    return None


def extract_text_with_runner(url: str, cdp_url=None, **kwargs):
    if not url.startswith("https://") and not url.startswith("http://"):
        url = f"https://{url}"

    with sync_playwright() as p:
        if not cdp_url:
            from django.conf import settings

            cdp_url = settings.PLAYWRIGHT_URL
        browser = p.chromium.connect(ws_endpoint=cdp_url)
        if kwargs.get("storage_state"):
            context = browser.new_context(storage_state=kwargs.get("storage_state"))
        else:
            context = browser.new_context()
        page = context.new_page()
        page.goto(url, timeout=kwargs.get("timeout", 30000))
        page_html = page.content()
        text = partition_html(text=page_html)
        return "\n".join(list(map(lambda x: str(x), text))) or "Could not extract text from URL"


def get_url_data(url: str, connection=None, **kwargs):
    if not url.startswith("https://") and not url.startswith("http://"):
        url = f"https://{url}"

    text = extract_text_from_url(
        url,
        extra_params=ExtraParams(openai_key=kwargs.get("openai_key"), connection=connection),
    )
    return text or "Could not extract text from URL"


class URLScraper(str, Enum):
    LOCAL = "local"

    def __str__(self):
        return str(self.value)


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
    extractor_method: Optional[URLScraper] = Field(default=URLScraper.LOCAL, json_schema_extra={"widget": "hidden"})

    @classmethod
    def slug(cls):
        return "url"

    @classmethod
    def provider_slug(cls):
        return "promptly"

    def get_data_documents(self, **kwargs):
        urls = self.urls.split("\n")
        urls = [url.strip().rstrip() for url_list in [url.split(",") for url in urls] for url in url_list]
        # Filter out empty urls
        urls = list(set(list(filter(lambda url: url != "", urls))))
        # Filter out sitemap.xml
        urls = list(filter(lambda url: not url.endswith(".xml"), urls))
        documents = []
        for url in urls:
            documents.append(
                DataDocument(
                    name=url,
                    content=url,
                    metadata={
                        "source": url,
                        "datasource_uuid": kwargs["datasource_uuid"],
                    },
                    datasource_uuid=kwargs["datasource_uuid"],
                    request_data=dict(connection_id=self.connection_id),
                )
            )
        return documents

    @classmethod
    def process_document(cls, document: DataDocument) -> DataDocument:
        connection_id = document.request_data.get("connection_id")

        connection_context = (
            get_connection_context(connection_id, document.metadata["datasource_uuid"]) if connection_id else None
        )
        url_text_data = extract_text_with_runner(
            document.content, connection=connection_id, storage_state=connection_context
        )

        text_data_uri = (
            f"data:text/plain;name={document.id_}_text.txt;base64,{base64.b64encode(url_text_data.encode()).decode()}"
        )
        text_file_objref = create_source_document_asset(
            text_data_uri,
            datasource_uuid=document.metadata["datasource_uuid"],
            document_id=str(uuid.uuid4()),
        )
        return document.model_copy(
            update={
                "text": url_text_data,
                "text_objref": text_file_objref,
            }
        )
