from typing import Optional, Union

import httpx
from openai._base_client import make_request_options
from openai._types import NOT_GIVEN, Body, Headers, NotGiven, Query
from openai.pagination import SyncPage
from openai.resources import Models as OpenAIModels

from ..constants import PROVIDER_GOOGLE, PROVIDER_STABILITYAI
from ..types import Model


class Models(OpenAIModels):
    def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Optional[Headers] = None,
        extra_query: Optional[Query] = None,
        extra_body: Optional[Body] = None,
        timeout: Union[float, httpx.Timeout, None, NotGiven] = NOT_GIVEN,
    ) -> SyncPage[Model]:
        """
        Lists the currently available models, and provides basic information about each
        one such as the owner and availability.
        """
        if self._client._llm_router_provider == PROVIDER_STABILITYAI:
            return self._get_api_list(
                "v1/engines/list",
                page=SyncPage[Model],
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                model=Model,
            )

        elif self._client._llm_router_provider == PROVIDER_GOOGLE:
            import google.generativeai as genai

            genai.configure(api_key=self._client.api_key)
            models = list(
                map(
                    lambda entry: Model(
                        id=entry.name, object="model", created=0, owned_by="", extra_data=entry.__dict__
                    ),
                    list(genai.list_models()),
                )
            )

            return SyncPage(data=models, object="list")

        return self._get_api_list(
            "/models",
            page=SyncPage[Model],
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            model=Model,
        )
