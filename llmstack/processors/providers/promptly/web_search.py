import logging
from enum import Enum
from typing import List

from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface, ApiProcessorSchema

logger = logging.getLogger(__name__)


class SearchEngine(str, Enum):
    GOOGLE = 'Google'

    def __str__(self):
        return self.value


class WebSearchConfiguration(ApiProcessorSchema):
    search_engine: SearchEngine = Field(
        default=SearchEngine.GOOGLE,
        description='Search engine to use',
        widget='customselect',
        advanced_parameter=True,
    )
    k: int = Field(
        default=5,
        description='Number of results to return',
        advanced_parameter=True,
    )


class WebSearchInput(ApiProcessorSchema):
    query: str = Field(..., description='Query to search for',
                       widget='textarea')


class WebSearchResult(ApiProcessorSchema):
    text: str
    source: str


class WebSearchOutput(ApiProcessorSchema):
    results: List[WebSearchResult] = Field(
        default=[], description='Search results')


class WebSearch(ApiProcessorInterface[WebSearchInput, WebSearchOutput, WebSearchConfiguration]):
    """
    Text summarizer API processor
    """

    def process_session_data(self, session_data):
        self._chat_history = session_data['chat_history'] if 'chat_history' in session_data else [
        ]
        self._context = session_data['context'] if 'context' in session_data else ''

    @staticmethod
    def name() -> str:
        return 'Web Search'

    @staticmethod
    def slug() -> str:
        return 'web_search'

    @staticmethod
    def description() -> str:
        return 'Search the web for answers'

    @staticmethod
    def provider_slug() -> str:
        return 'promptly'

    def process(self) -> dict:
        output_stream = self._output_stream

        query = self._input.query
        k = self._config.k

        search_url = f'https://www.google.com/search?q={query}'

        # Open playwright browser and search
        from playwright.sync_api import sync_playwright
        from django.conf import settings
        with sync_playwright() as p:
            browser = p.chromium.connect(ws_endpoint=settings.PLAYWRIGHT_URL) if hasattr(
                settings, 'PLAYWRIGHT_URL') and settings.PLAYWRIGHT_URL else p.chromium.launch()
            page = browser.new_page()
            page.goto(search_url)
            page.wait_for_selector('div#main')
            results = page.query_selector_all('div#main div.g')
            results = results[:k]
            results = list(map(lambda x: WebSearchResult(
                text=x.text_content(), source=x.query_selector('a').get_attribute('href')), results))
            browser.close()

        async_to_sync(output_stream.write)(WebSearchOutput(
            results=results
        ))

        output = output_stream.finalize()

        return output
