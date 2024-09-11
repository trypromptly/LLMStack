import base64
import json
import logging
import uuid
from typing import Optional

from langrocks.client import WebBrowser
from pydantic import Field
from unstructured.partition.auto import partition_html

from llmstack.common.blocks.base.schema import StrEnum
from llmstack.data.sources.base import BaseSource, DataDocument
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


def extract_text(html_page):
    elements = partition_html(text=html_page)
    return "\n".join(list(map(lambda x: x.text, elements))) or "Could not extract text from URL"


def get_page_html(url: str, **kwargs):
    page_html = "<html></html>"
    from django.conf import settings

    if not url.startswith("https://") and not url.startswith("http://"):
        url = f"https://{url}"

    try:
        with WebBrowser(f"{settings.RUNNER_HOST}:{settings.RUNNER_PORT}", html=True, interactive=False) as browser:
            page_html = browser.get_html(url=url)
    except Exception as e:
        logger.exception(f"Error while extracting page html: {e}")

    return page_html


class URLScraper(StrEnum):
    LOCAL = "local"
    LANGROCKS = "langrocks"


class URLSchema(BaseSource):
    urls: str = Field(
        description="URLs to scrape, List of URL can be comma or newline separated. If site.xml is present, it will be used to scrape the site.",
        max_length=1600,
        json_schema_extra={
            "widget": "webpageurls",
            "advanced_parameter": False,
        },
    )
    connection_id: Optional[str] = Field(
        default=None,
        description="Select connection if parsing loggedin page",
        json_schema_extra={
            "widget": "connection",
            "advanced_parameter": False,
        },
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
                    metadata={
                        "source": url,
                        "datasource_uuid": kwargs["datasource_uuid"],
                    },
                    datasource_uuid=kwargs["datasource_uuid"],
                    request_data=dict(connection_id=self.connection_id, url=url),
                    extra_info={"extra_data": self.get_extra_data()},
                )
            )
        return documents

    @classmethod
    def process_document(cls, document: DataDocument) -> DataDocument:
        connection_id = document.request_data.get("connection_id")

        connection_context = (
            get_connection_context(connection_id, document.metadata["datasource_uuid"]) if connection_id else None
        )
        url = document.name
        if document.request_data.get("url"):
            url = document.request_data.get("url")

        html_page = get_page_html(url, connection=connection_id, storage_state=connection_context)
        page_text = extract_text(html_page)

        text_data_uri = (
            f"data:text/plain;name={document.id_}_text.txt;base64,{base64.b64encode(page_text.encode()).decode()}"
        )
        html_data_uri = (
            f"data:text/html;name={document.id_}.html;base64,{base64.b64encode(html_page.encode()).decode()}"
        )
        content_file_objref = create_source_document_asset(
            html_data_uri,
            datasource_uuid=document.metadata["datasource_uuid"],
            document_id=str(uuid.uuid4()),
        )
        text_file_objref = create_source_document_asset(
            text_data_uri,
            datasource_uuid=document.metadata["datasource_uuid"],
            document_id=str(uuid.uuid4()),
        )
        return document.model_copy(
            update={
                "content": content_file_objref,
                "text": page_text,
                "text_objref": text_file_objref,
            }
        )
