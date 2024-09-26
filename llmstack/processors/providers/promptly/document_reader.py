import base64
import logging
from typing import List, Literal, Optional, Union

from asgiref.sync import async_to_sync
from django.conf import settings
from langrocks.client import WebBrowser
from langrocks.common.models.web_browser import WebBrowserCommand, WebBrowserCommandType
from pydantic import BaseModel, Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.utils.prequests import get, head
from llmstack.common.utils.text_extraction_service import (
    GoogleVisionTextExtractionService,
    PromptlyTextExtractionService,
)
from llmstack.common.utils.utils import generate_checksum, validate_parse_data_uri
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class PageSelectionAll(BaseModel):
    selection: Literal["all"] = "all"


class PageSelectionCustom(BaseModel):
    selection: Literal["custom"] = "custom"
    pages: str = Field(
        description="The pages to extract, this can be a range or a comma separated list of pages e.g 1-5,8,11-13"
    )

    @property
    def page_numbers(self):
        page_numbers = []
        for page in self.pages.split(","):
            if "-" in page:
                start, end = map(int, page.split("-"))
                page_numbers.extend(range(start, end + 1))
            else:
                page_numbers.append(int(page))
        return page_numbers


PageSelection = Union[PageSelectionAll, PageSelectionCustom]


class DocumentReaderInput(ApiProcessorSchema):
    input: str = Field(
        default="",
        description="The URL or file to extract data from, this can be a HTTP URL, d Data URL or a Promptly objref",
    )
    pages: PageSelection = Field(default=PageSelectionAll(), description="The pages to extract")
    search_query: Optional[str] = Field(default=None, description="Query to search the document")


class TextExtractorConfig(BaseModel):
    format_text: bool = Field(default=False)


class PromptlyTextExtractorConfig(TextExtractorConfig):
    provider: Literal["promptly"] = "promptly"


class GoogleTextExtractorConfig(TextExtractorConfig):
    provider: Literal["google"] = "google"


TextExtractorProviderConfigType = Union[PromptlyTextExtractorConfig, GoogleTextExtractorConfig]


class SearchConfig(BaseModel):
    def search(self, query, pages):
        return pages


class SimpleTextSearchConfig(BaseModel):
    type: Literal["simple"] = "simple"

    def search(self, query, pages):
        result = []
        query_terms = query.split(" ")
        for page in pages:
            for term in query_terms:
                if term in page.text:
                    result.append(page)
                    break
        return result


TextSearchConfigType = Union[SimpleTextSearchConfig]


class DocumentReaderConfiguration(ApiProcessorSchema):
    text_extractor_provider: TextExtractorProviderConfigType = Field(
        description="The text extractor provider", default=PromptlyTextExtractorConfig()
    )
    search_configuration: TextSearchConfigType = Field(
        description="The search configuration", default=SimpleTextSearchConfig()
    )
    connection_id: Optional[str] = Field(
        default=None,
        description="Connection to use",
        json_schema_extra={"advanced_parameter": False, "widget": "connection"},
    )
    use_browser: Optional[bool] = Field(description="Use browser for HTTP URI", default=False)


class DataPage(BaseModel):
    number: int
    text: str


class DocumentReaderOutput(ApiProcessorSchema):
    name: str = Field(default="", description="The name of the document")
    content: str = Field(
        default="",
        description="The extracted content",
    )
    pages: List[DataPage] = Field(default=[], description="The extracted pages")


class DocumentReader(ApiProcessorInterface[DocumentReaderInput, DocumentReaderOutput, DocumentReaderConfiguration]):
    @staticmethod
    def name() -> str:
        return "Document Reader"

    @staticmethod
    def slug() -> str:
        return "document_reader"

    @staticmethod
    def description() -> str:
        return "Reads text from a document"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    @classmethod
    def get_output_template(cls) -> Optional[OutputTemplate]:
        return OutputTemplate(markdown="""{{content}}""", jsonpath="$.content")

    def _get_url_bytes_mime_type(self, url: str):
        response = head(url)
        if response.status_code != 200:
            mime_type = "text/html"
        else:
            mime_type = response.headers.get("Content-Type", "text/html").split(";")[0]

        if mime_type.startswith("text/html") and self._config.use_browser:
            with WebBrowser(
                f"{settings.RUNNER_HOST}:{settings.RUNNER_PORT}",
                interactive=False,
                capture_screenshot=False,
                html=True,
                tags_to_extract=[],
                session_data=(
                    self._env["connections"][self._config.connection_id]["configuration"]["_storage_state"]
                    if self._config.connection_id
                    else ""
                ),
            ) as web_browser:
                browser_response = web_browser.run_commands(
                    [
                        WebBrowserCommand(
                            command_type=WebBrowserCommandType.GOTO,
                            data=url,
                        ),
                        WebBrowserCommand(
                            command_type=WebBrowserCommandType.WAIT,
                            selector="body",
                            data="5000",
                        ),
                    ]
                )
                content = browser_response.html.encode()
                mime_type = "text/html"
        else:
            response = get(url)
            content = response.content

        return url, base64.b64encode(content).decode(), mime_type

    def _get_data_url_bytes_mime_type(self, data_url: str):
        mime_type, filename, content = validate_parse_data_uri(data_url)
        return filename, content, mime_type

    def _get_objref_bytes_mime_type(self, objref: str):
        data_uri = self._get_session_asset_data_uri(objref, include_name=True)
        mime_type, filename, content = validate_parse_data_uri(data_uri)
        return filename, content, mime_type

    def filter_pages_based_on_search_query(self, pages, search_query, search_configuration):
        if search_query:
            return search_configuration.search(search_query, pages)
        return pages

    def filter_pages_based_on_page_selection(self, pages, page_selection):
        if isinstance(page_selection, PageSelectionCustom):
            page_numbers = page_selection.page_numbers
            return [page for page in pages if page.number in page_numbers]
        return pages

    def session_data_to_persist(self) -> dict:
        return {"document_pages": self._document_pages}

    def process_session_data(self, session_data):
        self._document_pages = session_data.get("document_pages", {})

    def process(self) -> str:
        input_uri = self._input.input
        content = None
        mime_type = None
        text_extractor = None
        file_checksum = None

        if input_uri.startswith("http"):
            content_name, content, mime_type = self._get_url_bytes_mime_type(input_uri)
            content = base64.b64decode(content)
        elif input_uri.startswith("data"):
            content_name, content, mime_type = self._get_data_url_bytes_mime_type(input_uri)
            content = base64.b64decode(content)
        elif input_uri.startswith("objref"):
            content_name, content, mime_type = self._get_objref_bytes_mime_type(input_uri)
            content = base64.b64decode(content)
        else:
            raise Exception("Invalid input")

        file_checksum = generate_checksum(content)

        if file_checksum in self._document_pages:
            document_pages = [DataPage(**page) for page in self._document_pages[file_checksum]]
        else:
            if self._config.text_extractor_provider.provider == "google":
                provider_config = self.get_provider_config(provider_slug="google")
                text_extractor = GoogleVisionTextExtractionService(
                    provider="google", service_account_json=provider_config.service_account_json
                )
            else:
                text_extractor = PromptlyTextExtractionService(provider="promptly")

            result = text_extractor.extract_from_bytes(content, filename=content_name, mime_type=mime_type)

            document_pages = list(
                map(
                    lambda x: DataPage(
                        number=x.page_no,
                        text=x.formatted_text if self._config.text_extractor_provider.format_text else x.text,
                    ),
                    result.pages,
                )
            )
            self._document_pages[file_checksum] = [page.model_dump() for page in document_pages]

        document_pages = self.filter_pages_based_on_page_selection(document_pages, self._input.pages)
        document_pages = self.filter_pages_based_on_search_query(
            document_pages, self._input.search_query, self._config.search_configuration
        )
        document_name = content_name
        document_content = "\n".join([page.text for page in document_pages])

        async_to_sync(self._output_stream.write)(
            DocumentReaderOutput(content=document_content, name=document_name, pages=document_pages)
        )

        return self._output_stream.finalize()
