import logging
import urllib
from typing import Any, Dict, List, Optional

from asgiref.sync import async_to_sync
from bs4 import BeautifulSoup
from langrocks.client import WebBrowser
from langrocks.common.models.web_browser import WebBrowserCommand, WebBrowserCommandType
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.blocks.base.schema import StrEnum
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.promptly.web_browser import BrowserRemoteSessionData

logger = logging.getLogger(__name__)


def parse_people_search_info(html_string):
    soup = BeautifulSoup(html_string, "html.parser")

    # Extract name
    name_tag = soup.find("span", {"aria-hidden": "true"})
    name = name_tag.text.strip() if name_tag else None

    # Extract LinkedIn profile URL
    profile_link_tag = soup.find("a", href=True, class_="app-aware-link")
    profile_url = profile_link_tag["href"] if profile_link_tag else None

    # Extract job title
    job_title_tag = soup.find("div", class_="entity-result__primary-subtitle")
    job_title = job_title_tag.text.strip() if job_title_tag else None

    # Extract location
    location_tag = soup.find("div", class_="entity-result__secondary-subtitle")
    location = location_tag.text.strip() if location_tag else None

    return {
        "name": name,
        "profile_url": profile_url.split("?")[0] if profile_url else None,
        "job_title": job_title,
        "location": location,
    }


def parse_job_search_info(html_string):
    soup = BeautifulSoup(html_string, "html.parser")

    # Extract job title using the aria-label attribute
    job_title_tag = soup.find("a", class_="job-card-list__title")
    job_title = job_title_tag["aria-label"].strip() if job_title_tag and job_title_tag.has_attr("aria-label") else None

    # Extract job URL from the href attribute
    job_url = job_title_tag["href"] if job_title_tag and job_title_tag.has_attr("href") else None
    if job_url and not job_url.startswith("http"):
        job_url = f"https://www.linkedin.com{job_url}"

    # Extract company name
    company_tag = soup.find("span", class_="job-card-container__primary-description")
    company_name = company_tag.text.strip() if company_tag else None

    # Extract location
    location_tag = soup.find("li", class_="job-card-container__metadata-item")
    location = location_tag.text.strip() if location_tag else None

    return {
        "job_title": job_title,
        "job_url": job_url,
        "company_name": company_name,
        "location": location,
    }


def parse_company_search_info(html_string):
    soup = BeautifulSoup(html_string, "html.parser")

    # Extract company name and URL
    company_tags = soup.find_all("a", class_="app-aware-link", href=True)
    company_name = None
    company_url = None
    for company_tag in company_tags:
        if company_tag and company_tag.text.strip():
            company_name = company_tag.text.strip()

        if company_tag and company_tag.has_attr("href"):
            company_url = company_tag["href"]

        if company_name and company_url:
            break

    # Extract company description (primary and secondary subtitles)
    description_tag = soup.find("div", class_="entity-result__primary-subtitle")
    description = description_tag.text.strip() if description_tag else None

    return {
        "company_name": company_name,
        "company_url": company_url,
        "description": description,
    }


class LinkedInEntity(StrEnum):
    PEOPLE = "people"
    COMPANIES = "companies"
    JOBS = "jobs"


class SearchInput(ApiProcessorSchema):
    keywords: str = Field(description="The company name to search for on LinkedIn")


class SearchOutput(ApiProcessorSchema):
    people: Optional[List[Dict[str, Any]]] = Field(description="The list of people found on LinkedIn", default=None)
    companies: Optional[List[Dict[str, Any]]] = Field(
        description="The list of companies found on LinkedIn", default=None
    )
    jobs: Optional[List[Dict[str, Any]]] = Field(description="The list of jobs found on LinkedIn", default=None)
    session: Optional[BrowserRemoteSessionData] = Field(
        default=None,
        description="Session data from the browser",
    )


class SearchConfiguration(ApiProcessorSchema):
    stream_video: bool = Field(description="Stream video", default=False)
    connection_id: Optional[str] = Field(
        description="The connection id to use for the search",
        default=None,
        json_schema_extra={"advanced_parameter": False, "widget": "connection"},
    )
    search_entity: LinkedInEntity = Field(description="The entity to search for", default=LinkedInEntity.PEOPLE)
    page_number: int = Field(description="The page number to start the search from", default=1)


def get_company_search_results(web_browser, search_params: dict):
    search_results = []
    url_encoded_search_params = urllib.parse.urlencode(search_params)
    browser_response = web_browser.run_commands(
        commands=[
            WebBrowserCommand(
                command_type=WebBrowserCommandType.GOTO,
                data=f"https://www.linkedin.com/search/results/companies/?{url_encoded_search_params}",
            ),
            WebBrowserCommand(
                command_type=WebBrowserCommandType.WAIT,
                selector="div.search-results-container",
                data="2000",
            ),
        ]
    )
    soup = BeautifulSoup(browser_response.html, "html.parser")
    results = soup.select("div.search-results-container li")

    if results:
        for result in results:
            result_info = parse_company_search_info(result.prettify())
            search_results.append(result_info)
    return search_results


def get_job_search_results(web_browser, search_params: dict):
    search_results = []
    url_encoded_search_params = urllib.parse.urlencode(search_params)
    browser_response = web_browser.run_commands(
        commands=[
            WebBrowserCommand(
                command_type=WebBrowserCommandType.GOTO,
                data=f"https://www.linkedin.com/jobs/search/?{url_encoded_search_params}",
            ),
            WebBrowserCommand(
                command_type=WebBrowserCommandType.WAIT,
                selector="div.jobs-search-results-list",
                data="2000",
            ),
        ]
    )
    soup = BeautifulSoup(browser_response.html, "html.parser")
    results = soup.select("div.jobs-search-results-list li")
    if results:
        for result in results:
            result_info = parse_job_search_info(result.prettify())
            search_results.append(result_info)
    return search_results


def get_people_search_results(web_browser, search_params: dict):
    search_results = []
    url_encoded_search_params = urllib.parse.urlencode(search_params)
    browser_response = web_browser.run_commands(
        commands=[
            WebBrowserCommand(
                command_type=WebBrowserCommandType.GOTO,
                data=f"https://www.linkedin.com/search/results/people/?{url_encoded_search_params}",
            ),
            WebBrowserCommand(
                command_type=WebBrowserCommandType.WAIT,
                selector="div.search-results-container",
                data="2000",
            ),
        ]
    )
    soup = BeautifulSoup(browser_response.html, "html.parser")
    results = soup.select("div.search-results-container li")
    if results:
        for result in results:
            result_info = parse_people_search_info(result.prettify())
            search_results.append(result_info)
    return search_results


class SearchProcessor(ApiProcessorInterface[SearchInput, SearchOutput, SearchConfiguration]):
    @staticmethod
    def name() -> str:
        return "Search"

    @staticmethod
    def slug() -> str:
        return "search"

    @staticmethod
    def description() -> str:
        return "Search on LinkedIn"

    @staticmethod
    def provider_slug() -> str:
        return "linkedin"

    @classmethod
    def get_output_template(cls) -> OutputTemplate | None:
        return OutputTemplate(
            markdown="""<promptly-web-browser-embed wsUrl="{{session.ws_url}}"></promptly-web-browser-embed>""",
            jsonpath="$.people",
        )

    def process(self) -> dict:
        from django.conf import settings

        with WebBrowser(
            f"{settings.RUNNER_HOST}:{settings.RUNNER_PORT}",
            interactive=self._config.stream_video,
            capture_screenshot=False,
            html=True,
            session_data=(
                self._env["connections"][self._config.connection_id]["configuration"]["_storage_state"]
                if self._config.connection_id
                else ""
            ),
        ) as web_browser:
            if self._config.stream_video and web_browser.get_wss_url():
                async_to_sync(
                    self._output_stream.write,
                )(
                    SearchOutput(
                        session=BrowserRemoteSessionData(
                            ws_url=web_browser.get_wss_url(),
                        ),
                    ),
                )
            job_search_results = []
            people_search_results = []
            company_search_results = []

            if self._config.search_entity == LinkedInEntity.PEOPLE:
                people_search_results = get_people_search_results(
                    web_browser, self._input.model_dump(include=["keywords"])
                )

            elif self._config.search_entity == LinkedInEntity.JOBS:
                job_search_results = get_job_search_results(web_browser, self._input.model_dump(include=["keywords"]))
            elif self._config.search_entity == LinkedInEntity.COMPANIES:
                company_search_results = get_company_search_results(
                    web_browser, self._input.model_dump(include=["keywords"])
                )

            async_to_sync(self._output_stream.write)(
                SearchOutput(companies=company_search_results, people=people_search_results, jobs=job_search_results)
            )

            return self._output_stream.finalize()
