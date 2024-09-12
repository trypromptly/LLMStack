import logging
from typing import Optional

from asgiref.sync import async_to_sync
from bs4 import BeautifulSoup
from langrocks.client import WebBrowser
from langrocks.common.models.web_browser import WebBrowserCommand, WebBrowserCommandType
from pydantic import BaseModel, Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.utils.text_extraction_service import PromptlyTextExtractionService
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.promptly.web_browser import BrowserRemoteSessionData

logger = logging.getLogger(__name__)

text_extraction_service = PromptlyTextExtractionService()


class JobDetailsInput(ApiProcessorSchema):
    job_url: str = Field(description="The job URL", default="")


class LinkedInJob(BaseModel):
    title: Optional[str] = Field(description="The job title", default=None)
    description: Optional[str] = Field(description="The job description", default=None)


class JobDetailOutput(ApiProcessorSchema):
    job: Optional[LinkedInJob] = Field(description="The job details", default=None)
    error: Optional[str] = Field(
        default=None,
        description="Error message if something went wrong",
    )
    session: Optional[BrowserRemoteSessionData] = Field(
        default=None,
        description="Session data from the browser",
    )


class JobDetailConfiguration(ApiProcessorSchema):
    connection_id: Optional[str] = Field(
        default=None,
        description="LinkedIn login session connection to use",
        json_schema_extra={"advanced_parameter": False, "widget": "connection"},
    )
    get_page_screenshot: bool = Field(
        description="Whether to get a screenshot of the job details page",
        default=False,
        json_schema_extra={"advanced_parameter": True},
    )
    stream_video: bool = Field(description="Stream video", default=False)


def get_linkedin_job_detail(job_url, web_browser):
    job_detail = {}
    browser_response = web_browser.run_commands(
        [
            WebBrowserCommand(
                command_type=WebBrowserCommandType.GOTO,
                data=job_url,
            ),
            WebBrowserCommand(
                command_type=WebBrowserCommandType.WAIT,
                data="2000",
            ),
        ]
    )
    soup = BeautifulSoup(browser_response.html, "html.parser")
    title = soup.select("head title")
    if title and title[0]:
        job_detail["title"] = title[0].text.split("|")[0]

    description_div = soup.select("div.description__text")
    if description_div and description_div[0]:
        # This is from logged out page
        job_detail["description"] = text_extraction_service.extract_from_bytes(
            description_div[0].encode(), mime_type="text/html", filename="file.html"
        ).text

    jobs_description_content_div = soup.select("div.jobs-description-content__text")
    if jobs_description_content_div and jobs_description_content_div[0]:
        # This is from logged in page
        job_detail["description"] = text_extraction_service.extract_from_bytes(
            jobs_description_content_div[0].encode(), mime_type="text/html", filename="file.html"
        ).text

    return job_detail


class JobDetailProcessor(ApiProcessorInterface[JobDetailsInput, JobDetailOutput, JobDetailConfiguration]):
    @staticmethod
    def name() -> str:
        return "Job Detail"

    @staticmethod
    def slug() -> str:
        return "job_detail"

    @staticmethod
    def description() -> str:
        return "Gets job listing details from the URL."

    @staticmethod
    def provider_slug() -> str:
        return "linkedin"

    @classmethod
    def get_output_template(cls) -> Optional[OutputTemplate]:
        return OutputTemplate(
            markdown="""<promptly-web-browser-embed wsUrl="{{session.ws_url}}"></promptly-web-browser-embed>""",
            jsonpath="$.job",
        )

    def process(self) -> dict:
        from django.conf import settings

        with WebBrowser(
            f"{settings.RUNNER_HOST}:{settings.RUNNER_PORT}",
            interactive=self._config.stream_video,
            capture_screenshot=self._config.get_page_screenshot,
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
                    JobDetailOutput(
                        session=BrowserRemoteSessionData(
                            ws_url=web_browser.get_wss_url(),
                        ),
                    ),
                )
            job = get_linkedin_job_detail(self._input.job_url, web_browser)
            if job:
                async_to_sync(self._output_stream.write)(JobDetailOutput(job=LinkedInJob(**job)))
            else:
                async_to_sync(self._output_stream.write)(JobDetailOutput(error="Failed to get job details"))
        return self._output_stream.finalize()
