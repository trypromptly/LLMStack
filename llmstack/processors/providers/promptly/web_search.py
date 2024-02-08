from enum import Enum
from typing import List, Optional

import requests
from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)


class SearchEngine(str, Enum):
    GOOGLE = "Google"

    def __str__(self):
        return self.value


class WebSearchConfiguration(ApiProcessorSchema):
    search_engine: SearchEngine = Field(
        default=SearchEngine.GOOGLE,
        description="Search engine to use",
        widget="customselect",
        advanced_parameter=True,
    )
    k: int = Field(
        default=5,
        description="Number of results to return",
        advanced_parameter=True,
    )


class WebSearchInput(ApiProcessorSchema):
    query: str = Field(
        default="",
        description="Query to search for",
        widget="textarea",
    )


class WebSearchResult(ApiProcessorSchema):
    text: str = Field(default="", description="Text of the result")
    source: str = Field(default="", description="Source URL of the result")


class WebSearchOutput(ApiProcessorSchema):
    results: List[WebSearchResult] = Field(
        default=[],
        description="Search results",
    )


class WebSearch(
    ApiProcessorInterface[WebSearchInput, WebSearchOutput, WebSearchConfiguration],
):
    """
    Text summarizer API processor
    """

    def process_session_data(self, session_data):
        self._chat_history = session_data["chat_history"] if "chat_history" in session_data else []
        self._context = session_data["context"] if "context" in session_data else ""

    @staticmethod
    def name() -> str:
        return "Web Search"

    @staticmethod
    def slug() -> str:
        return "web_search"

    @staticmethod
    def description() -> str:
        return "Search the web for answers"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    @classmethod
    def get_output_template(cls) -> Optional[OutputTemplate]:
        return OutputTemplate(
            markdown="""{% for result in results %}
{{result.text}}
{{result.source}}

{% endfor %}""",
        )

    async def _get_results_with_playwright(self, search_url, k):
        from django.conf import settings
        from playwright.async_api import async_playwright

        async with async_playwright() as playwright:
            browser = (
                await playwright.chromium.connect(ws_endpoint=settings.PLAYWRIGHT_URL)
                if hasattr(settings, "PLAYWRIGHT_URL") and settings.PLAYWRIGHT_URL
                else await playwright.chromium.launch(args=["--disable-blink-features=AutomationControlled"])
            )
            page = await browser.new_page()
            await page.goto(search_url)
            await page.wait_for_selector("div#main")
            results = await page.query_selector_all("div#main div.g")
            results = results[:k]
            output = []
            for result in results:
                a = await result.query_selector("a")
                href = await a.get_attribute("href")
                text = await result.text_content()
                output.append(WebSearchResult(text=text, source=href))

            await browser.close()
            return output

    def process(self) -> dict:
        output_stream = self._output_stream
        api_key = self._env.get("google_custom_search_api_key", None)
        cx = self._env.get("google_custom_search_cx", None)

        query = self._input.query
        k = self._config.k
        if api_key and cx:
            # Use Google Custom Search API
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": api_key,
                "cx": cx,
                "q": query,
            }
            response = requests.get(url, params=params)
            if response.ok:
                response_data = response.json()
                items = response_data.get("items", [])
                results = []
                for item in items:
                    results.append(
                        WebSearchResult(
                            text=f"{item['title']}. {item['snippet']}",
                            source=item["link"],
                        ),
                    )
            else:
                results = []
        else:
            # Fallback to playwright
            search_url = f"https://www.google.com/search?q={query}"
            results = async_to_sync(
                self._get_results_with_playwright,
            )(search_url, k)

        async_to_sync(output_stream.write)(
            WebSearchOutput(
                results=results,
            ),
        )

        output = output_stream.finalize()

        return output
