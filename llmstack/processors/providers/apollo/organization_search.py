import logging
import urllib.parse
from typing import Any, Dict, List, Optional

from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.utils import prequests
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.apollo.people_search import APIResponse
from llmstack.processors.providers.metrics import MetricType

logger = logging.getLogger(__name__)


class OrganizationSearchInput(ApiProcessorSchema):
    organization_ids: Optional[List[str]] = Field(
        description="An array of organization ids obtained from companies-search",
        default=None,
        examples=["5f5e2b4b4f6f6b001f3b4b4f"],
    )
    organization_num_employees_ranges: Optional[List[str]] = Field(
        description="An array of intervals to include organizations having number of employees in a range",
        default=None,
        examples=["1-10", "11-50"],
    )
    organization_locations: Optional[List[str]] = Field(
        description="An array of locations to include organizations having locations in",
        examples=["San Francisco, CA", "New York, NY"],
        default=None,
    )
    organization_not_locations: Optional[List[str]] = Field(
        description="An array of locations to exclude organizations having locations in",
        examples=["San Francisco, CA", "New York, NY"],
        default=None,
    )
    q_organization_keyword_tags: Optional[List[str]] = Field(
        description="An array of organization keyword tags to include organizations having",
        examples=["sales strategy", "lead"],
        default=None,
    )
    q_organization_name: Optional[str] = Field(
        description="A string to search for in the organization name",
        examples=["Apollo"],
        default=None,
    )


class OrganizationSearchOutput(ApiProcessorSchema):
    breadcrumbs: Optional[List[Dict[str, str]]] = Field(description="The breadcrumbs for the API call", default=[])
    accounts: Optional[List[Dict[str, Any]]] = Field(description="The list of accounts from the API call", default=[])
    organizations: Optional[List[Dict[str, Any]]] = Field(
        description="The list of organizations from the API call", default=[]
    )
    api_response: APIResponse = Field(description="The  response from the API call", default={})


class PeopleSearchOutput(ApiProcessorSchema):
    breadcrumbs: Optional[List[Dict[str, str]]] = Field(description="The breadcrumbs for the API call", default=[])
    people: Optional[List[Dict[str, Any]]] = Field(description="The list of people from the API call", default=[])
    contacts: Optional[List[Dict[str, Any]]] = Field(description="The list of contacts for the API call", default=[])
    api_response: APIResponse = Field(description="The  response from the API call", default={})


class OrganizationSearchConfiguration(ApiProcessorSchema):
    page: Optional[int] = Field(
        description="The page number to return",
        default=1,
    )
    page_size: Optional[int] = Field(
        description="The number of results to return per page",
        default=10,
    )


class OrganizationSearch(
    ApiProcessorInterface[OrganizationSearchInput, OrganizationSearchOutput, OrganizationSearchConfiguration]
):
    """
    Organization search processor
    """

    @staticmethod
    def name() -> str:
        return "Organization Search"

    @staticmethod
    def slug() -> str:
        return "organization_search"

    @staticmethod
    def description() -> str:
        return "Search for an organization"

    @staticmethod
    def provider_slug() -> str:
        return "apollo"

    @classmethod
    def get_output_template(cls) -> OutputTemplate | None:
        return OutputTemplate(
            markdown="{{api_response.response}}",
            jsonpath="$.accounts",
        )

    def process(self) -> dict:
        provider_config = self.get_provider_config(provider_slug=self.provider_slug())
        api_key = provider_config.api_key

        query_params_str = ""
        for key, values in self._input.model_dump().items():
            if not values:
                continue

            values = (
                [urllib.parse.quote(value) for value in values]
                if isinstance(values, list)
                else urllib.parse.quote(str(values))
            )

            if key == "organization_num_employees_ranges":
                query_params_str += f"&organization_num_employees_ranges[]={','.join(values)}"
            elif key == "organization_locations":
                query_params_str += f"&organization_locations[]={','.join(values)}"
            elif key == "organization_not_locations":
                query_params_str += f"&organization_not_locations[]={','.join(values)}"
            elif key == "q_organization_keyword_tags":
                query_params_str += f"&q_organization_keyword_tags[]={','.join(values)}"
            elif key == "q_organization_name":
                query_params_str += f"&q_organization_name={values}"
            elif key == "organization_ids":
                query_params_str += f"&organization_ids[]={','.join(values)}"

        if query_params_str:
            query_params_str = "?" + query_params_str[1:]

        query_url = f"https://api.apollo.io/api/v1/mixed_companies/search{query_params_str}&page={self._config.page}&per_page={self._config.page_size}"

        response = prequests.post(
            url=query_url,
            headers={"Cache-Control": "no-cache", "Content-Type": "application/json", "X-Api-Key": api_key},
        )

        if response.ok:
            self._usage_data.append(
                ("apollo/*/*/*", MetricType.API_INVOCATION, (provider_config.provider_config_source, 1))
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
            OrganizationSearchOutput(
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
                accounts=response_json.get("accounts", []),
                organizations=response_json.get("organizations", []),
            )
        )

        output = self._output_stream.finalize()
        return output
