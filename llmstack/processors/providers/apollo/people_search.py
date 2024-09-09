import logging
from typing import Any, Dict, List, Optional

from asgiref.sync import async_to_sync
from pydantic import BaseModel, Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.utils import prequests
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.metrics import MetricType

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


class APIResponse(BaseModel):
    response: str = Field(description="The response from the API call as a string", default="")
    response_json: Optional[Dict[str, Any]] = Field(
        description="The response from the API call as a JSON object", default={}
    )
    headers: Optional[Dict[str, str]] = Field(description="The headers from the API call", default={})
    code: int = Field(description="The status code from the API call", default=200)
    size: int = Field(description="The size of the response from the API call", default=0)
    time: float = Field(description="The time it took to get the response from the API call", default=0.0)


class PeopleSearchOutput(ApiProcessorSchema):
    breadcrumbs: Optional[List[Dict[str, str]]] = Field(description="The breadcrumbs for the API call", default=[])
    people: Optional[List[Dict[str, Any]]] = Field(description="The list of people from the API call", default=[])
    contacts: Optional[List[Dict[str, Any]]] = Field(description="The list of contacts for the API call", default=[])
    api_response: APIResponse = Field(description="The  response from the API call", default={})


class PeopleSearchConfiguration(ApiProcessorSchema):
    connection_id: Optional[str] = Field(
        default=None,
        description="The connection id to use for the API call",
        json_schema_extra={"widget": "hidden"},
    )
    max_results: Optional[int] = Field(
        description="The maximum number of results to return",
        default=10,
        le=100,
        ge=10,
        multiple_of=10,
        json_schema_extra={"advanced_parameter": False},
    )
    page: Optional[int] = Field(
        description="The page number to return",
        default=None,
    )
    page_size: Optional[int] = Field(description="The number of results to return per page", default=None, le=20, ge=10)


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
            markdown="{{api_response.response}}",
        )

    def process(self) -> dict:
        data = self._input.model_dump()
        data["page"] = self._config.page or 1
        data["per_page"] = self._config.page_size or self._config.max_results or 10

        for key in data:
            if not data[key]:
                data[key] = None

        provider_config = self.get_provider_config(provider_slug=self.provider_slug())
        api_key = provider_config.api_key

        response = prequests.post(
            url="https://api.apollo.io/v1/mixed_people/search",
            json=data,
            headers={"Cache-Control": "no-cache", "Content-Type": "application/json", "X-Api-Key": api_key},
        )
        if response.ok:
            self._usage_data.append(
                (
                    "apollo/*/*/*",
                    MetricType.API_INVOCATION,
                    (provider_config.provider_config_source, self._config.max_results // 10),
                )
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
                api_response=APIResponse(
                    response=response_text,
                    response_json=response_json,
                    response_objref=objref,
                    headers=dict(response.headers),
                    code=response.status_code,
                    size=len(response.text),
                    time=response.elapsed.total_seconds(),
                ),
                breadcrumbs=response_json.get("breadcrumbs", []),
                people=response_json.get("people", []),
                contacts=response_json.get("contacts", []),
            )
        )

        output = self._output_stream.finalize()
        return output
