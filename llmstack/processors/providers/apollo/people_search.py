import logging
from typing import Any, Dict, List, Optional

from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.utils import prequests
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class PeopleSearchInput(ApiProcessorSchema):
    person_titles: Optional[List[str]] = Field(
        description="An array of the person's title. Apollo will return results matching ANY of the titles passed in",
        default=None,
        examples=["sales director", "engineer manager"],
    )
    q_keywords: Optional[str] = Field(
        description="A string of words over which we want to filter the results",
        examples=["Tim"],
        default=None,
    )
    person_locations: Optional[List[str]] = Field(
        description="An array of locations to include people having locations in",
        examples=["San Francisco, CA", "New York, NY"],
        default=None,
    )
    person_seniorities: Optional[List[str]] = Field(
        description="An array of seniorities to include people having seniorities in",
        examples=["Entry", "Senior"],
        default=None,
    )
    contact_email_status: Optional[List[str]] = Field(
        description="An array of strings to look for people having a set of email statuses",
        examples=["verified", "guessed", "unavailable", "bounced", "pending_manual_fulfillment"],
        default=["verified", "guessed", "unavailable", "pending_manual_fulfillment"],
    )
    q_organization_domains: Optional[List[str]] = Field(
        description="An array of the company domains to search for, joined by the new line character.",
        examples=["apollo.io", "google.com"],
        default=None,
    )
    organization_locations: Optional[List[str]] = Field(
        description="An array of locations to include organizations having locations in",
        examples=["San Francisco, CA", "New York, NY"],
        default=None,
    )
    organization_ids: Optional[List[str]] = Field(
        description="An array of organization ids obtained from organizations-search",
        examples=["5f5e2b4b4f6f6b001f3b4b4f"],
        default=None,
    )
    organization_num_employees_ranges: Optional[List[str]] = Field(
        description="An array of intervals to include organizations having number of employees in a range",
        default=None,
        examples=["1-10", "11-50"],
    )


class PeopleSearchOutput(ApiProcessorSchema):
    response: str = Field(description="The response from the API call as a string", default="")
    response_json: Optional[Dict[str, Any]] = Field(
        description="The response from the API call as a JSON object", default={}
    )
    headers: Optional[Dict[str, str]] = Field(description="The headers from the API call", default={})
    code: int = Field(description="The status code from the API call", default=200)
    size: int = Field(description="The size of the response from the API call", default=0)
    time: float = Field(description="The time it took to get the response from the API call", default=0.0)


class PeopleSearchConfiguration(ApiProcessorSchema):
    connection_id: Optional[str] = Field(
        description="The connection id to use for the API call",
        json_schema_extra={"advanced_parameter": False, "widget": "connection"},
    )
    page: Optional[int] = Field(
        description="The page number to return",
        default=1,
    )
    page_size: Optional[int] = Field(
        description="The number of results to return per page",
        default=10,
    )


class PeopleSearch(ApiProcessorInterface[PeopleSearchInput, PeopleSearchOutput, PeopleSearchConfiguration]):
    """
    People search processor
    """

    @staticmethod
    def name() -> str:
        return "People Search"

    @staticmethod
    def slug() -> str:
        return "people_search"

    @staticmethod
    def description() -> str:
        return "Search for people"

    @staticmethod
    def provider_slug() -> str:
        return "apollo"

    @classmethod
    def get_output_template(cls) -> OutputTemplate | None:
        return OutputTemplate(
            markdown="{{response}}",
        )

    def process(self) -> dict:
        data = self._input.model_dump()
        data["page"] = self._config.page
        data["per_page"] = self._config.page_size

        for key in data:
            if not data[key]:
                data[key] = None

        connection = (
            self._env["connections"].get(
                self._config.connection_id,
                None,
            )
            if self._config.connection_id
            else None
        )
        logger.info(f"Data: {data}")
        response = prequests.post(
            url="https://api.apollo.io/v1/mixed_people/search",
            json=data,
            _connection=connection,
            headers={"Cache-Control": "no-cache", "Content-Type": "application/json"},
        )

        objref = None
        response_text = response.text
        response_json = None
        try:
            if response.json():
                response_json = response.json()
                if isinstance(response_json, list):
                    response_json = {"data": response.json()}
        except Exception:
            pass

        async_to_sync(self._output_stream.write)(
            PeopleSearchOutput(
                response=response_text,
                response_json=response_json,
                response_objref=objref,
                headers=dict(response.headers),
                code=response.status_code,
                size=len(response.text),
                time=response.elapsed.total_seconds(),
            )
        )

        output = self._output_stream.finalize()
        return output
