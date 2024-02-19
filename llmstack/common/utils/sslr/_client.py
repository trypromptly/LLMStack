import os
from typing import Any, Literal, Mapping, Optional, Type, Union, overload

import httpx
from openai import OpenAI
from openai._client import SyncAPIClient
from openai._models import FinalRequestOptions
from openai._utils import is_given
from openai.lib.azure import AzureADTokenProvider
from typing_extensions import override

from ._exceptions import LLMError
from ._response import LLMResponse
from ._streaming import AsyncStream, LLMGRPCStream, LLMRestStream
from ._types import NOT_GIVEN, NotGiven, ResponseT, Timeout
from ._utils import LLMHttpResponse, is_mapping
from .constants import (
    DEFAULT_MAX_RETRIES,
    PROVIDER_AZURE_OPENAI,
    PROVIDER_GOOGLE,
    PROVIDER_LOCALAI,
    PROVIDER_OPENAI,
    PROVIDER_STABILITYAI,
)
from .resources import Audio, Chat, Completions, Embeddings, Images, Models


class LLMClient(SyncAPIClient):
    @override
    def _build_request(
        self,
        options: FinalRequestOptions,
    ) -> httpx.Request:
        if self._llm_router_provider == PROVIDER_AZURE_OPENAI:
            _deployments_endpoints = set(
                [
                    "/completions",
                    "/chat/completions",
                    "/embeddings",
                    "/audio/transcriptions",
                    "/audio/translations",
                ]
            )
            if options.url in _deployments_endpoints and is_mapping(options.json_data):
                model = options.json_data.get("model")
                if model is not None and "/deployments" not in str(self.base_url):
                    options.url = f"/deployments/{model}{options.url}"

        return super()._build_request(options)

    @override
    def _process_response(
        self,
        *,
        cast_to: Type[ResponseT],
        options: FinalRequestOptions,
        response: httpx.Response,
        stream: bool,
        stream_cls: Union[type[LLMRestStream], type[AsyncStream[Any]], None],
    ) -> ResponseT:
        if self._llm_router_provider == PROVIDER_STABILITYAI:
            if response.is_success and response.request.url.path.endswith("/engines/list"):
                models = response.json()
                result = {"object": "list", "data": models}
                modified_response = LLMHttpResponse(response=response, json=result)
                api_response = LLMResponse(
                    raw=modified_response,
                    client=self,
                    cast_to=cast_to,
                    stream=stream,
                    stream_cls=stream_cls,
                    options=options,
                )
                return api_response.parse()

        return super()._process_response(
            cast_to=cast_to,
            options=options,
            response=response,
            stream=stream,
            stream_cls=stream_cls,
        )


class LLM(LLMClient, OpenAI):
    completions: Completions
    chat: Chat
    embeddings: Embeddings
    images: Images
    audio: Audio
    models: Models

    # Stability AI options
    @overload
    def __init__(
        self,
        *,
        stabilityai_api_key: str,
        base_url: str,
        organization: Optional[str] = None,
        stability_client_id: Optional[str] = None,
        stability_client_version: Optional[str] = None,
        timeout: Union[float, Timeout, None, NotGiven] = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Optional[Mapping[str, str]] = None,
        default_query: Optional[Mapping[str, object]] = None,
        http_client: Optional[httpx.Client] = None,
        _strict_response_validation: bool = False,
    ) -> None:
        ...

    # Google Gemini options
    @overload
    def __init__(
        self,
        *,
        google_api_key: str,
        timeout: Union[float, Timeout, None, NotGiven] = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Optional[Mapping[str, str]] = None,
        default_query: Optional[Mapping[str, object]] = None,
        http_client: Optional[httpx.Client] = None,
        _strict_response_validation: bool = False,
    ) -> None:
        ...

    # Azure OpenAI options
    @overload
    def __init__(
        self,
        *,
        azure_endpoint: str,
        azure_deployment: Optional[str] = None,
        api_version: Optional[str] = None,
        api_key: Optional[str] = None,
        azure_ad_token: Optional[str] = None,
        azure_ad_token_provider: Optional[AzureADTokenProvider] = None,
        organization: Optional[str] = None,
        timeout: Union[float, Timeout, None, NotGiven] = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Optional[Mapping[str, str]] = None,
        default_query: Optional[Mapping[str, object]] = None,
        http_client: Optional[httpx.Client] = None,
        _strict_response_validation: bool = False,
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        *,
        azure_deployment: Optional[str] = None,
        api_version: Optional[str] = None,
        api_key: Optional[str] = None,
        azure_ad_token: Optional[str] = None,
        azure_ad_token_provider: Optional[AzureADTokenProvider] = None,
        organization: Optional[str] = None,
        timeout: Union[float, Timeout, None, NotGiven] = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Optional[Mapping[str, str]] = None,
        default_query: Optional[Mapping[str, object]] = None,
        http_client: Optional[httpx.Client] = None,
        _strict_response_validation: bool = False,
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        *,
        base_url: str,
        api_version: Optional[str] = None,
        api_key: Optional[str] = None,
        azure_ad_token: Optional[str] = None,
        azure_ad_token_provider: Optional[AzureADTokenProvider] = None,
        organization: Optional[str] = None,
        timeout: Union[float, Timeout, None, NotGiven] = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Optional[Mapping[str, str]] = None,
        default_query: Optional[Mapping[str, object]] = None,
        http_client: Optional[httpx.Client] = None,
        _strict_response_validation: bool = False,
    ) -> None:
        ...

    def __init__(
        self,
        *,
        provider: Union[
            Literal["openai"], Literal["azure-openai"], Literal["google"], Literal["stability-ai"], Literal["localai"]
        ] = PROVIDER_OPENAI,
        api_version: Optional[str] = None,
        openai_api_version: Optional[str] = None,
        stability_ai_api_version: Optional[str] = None,
        azure_openai_api_version: Optional[str] = None,
        azure_endpoint: Optional[str] = None,
        azure_deployment: Optional[str] = None,
        api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        localai_api_key: Optional[str] = None,
        azure_api_key: Optional[str] = None,
        google_api_key: Optional[str] = None,
        stabilityai_api_key: Optional[str] = None,
        azure_ad_token: Optional[str] = None,
        azure_ad_token_provider: Optional[AzureADTokenProvider] = None,
        organization: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Union[float, Timeout, None, NotGiven] = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Optional[Mapping[str, str]] = None,
        default_query: Optional[Mapping[str, object]] = None,
        http_client: Optional[httpx.Client] = None,
        _strict_response_validation: bool = False,
    ) -> None:
        self._llm_router_provider = provider

        if provider == PROVIDER_OPENAI:
            base_url = base_url if base_url else "https://api.openai.com/v1"
            api_key = openai_api_key
            api_version = openai_api_version

        elif provider == PROVIDER_AZURE_OPENAI:
            api_key = azure_api_key

            if azure_ad_token is None:
                azure_ad_token = os.environ.get("AZURE_OPENAI_AD_TOKEN")

            if api_key is None and azure_ad_token is None and azure_ad_token_provider is None:
                raise LLMError(
                    "Missing credentials. Please pass one of `api_key`, `azure_ad_token`, `azure_ad_token_provider`, or the `AZURE_OPENAI_API_KEY` or `AZURE_OPENAI_AD_TOKEN` environment variables."
                )

            if azure_openai_api_version:
                api_version = azure_openai_api_version

            if api_version is None:
                raise ValueError("api_version is required for azure-openai")

            if default_query is None:
                default_query = {"api-version": api_version}
            else:
                default_query = {"api-version": api_version, **default_query}

            if base_url is None:
                if azure_endpoint is None:
                    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")

                if azure_endpoint is None:
                    raise ValueError(
                        "Must provide one of the `base_url` or `azure_endpoint` arguments, or the `AZURE_OPENAI_ENDPOINT` environment variable"
                    )

                if azure_deployment is not None:
                    base_url = f"{azure_endpoint}/openai/deployments/{azure_deployment}"
                else:
                    base_url = f"{azure_endpoint}/openai"
            else:
                if azure_endpoint is not None:
                    raise ValueError("base_url and azure_endpoint are mutually exclusive")

        elif provider == PROVIDER_STABILITYAI:
            if stability_ai_api_version:
                api_version = stability_ai_api_version

            api_key = stabilityai_api_key

            if not base_url:
                base_url = "https://api.stability.ai/"

        elif provider == PROVIDER_LOCALAI:
            if base_url is None:
                raise ValueError("base_url is required for localai")

            api_key = localai_api_key

        elif provider == PROVIDER_GOOGLE:
            api_key = google_api_key

        if api_key is None:
            # define a sentinel value to avoid any typing issues
            raise ValueError("api_key is required")

        self.api_key = api_key
        self.organization = organization

        super().__init__(
            api_key=api_key,
            organization=organization,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
            default_query=default_query,
            http_client=http_client,
            _strict_response_validation=_strict_response_validation,
        )

        self._default_stream_cls = LLMRestStream
        if provider == PROVIDER_GOOGLE:
            self._default_stream_cls = LLMGRPCStream

        self.chat = Chat(self)
        self.embeddings = Embeddings(self)
        self.images = Images(self)
        self.audio = Audio(self)
        self.models = Models(self)

        if provider == PROVIDER_AZURE_OPENAI:
            self._azure_ad_token = azure_ad_token
            self._azure_ad_token_provider = azure_ad_token_provider

    def _get_azure_ad_token(self) -> Optional[str]:
        if self._azure_ad_token is not None:
            return self._azure_ad_token

        provider = self._azure_ad_token_provider
        if provider is not None:
            token = provider()
            if not token or not isinstance(token, str):  # pyright: ignore[reportUnnecessaryIsInstance]
                raise ValueError(
                    f"Expected `azure_ad_token_provider` argument to return a string but it returned {token}",
                )
            return token

        return None

    @override
    def _prepare_options(self, options: FinalRequestOptions) -> None:
        headers: dict = {**options.headers} if is_given(options.headers) else {}
        options.headers = headers
        azure_ad_token = None

        if self._llm_router_provider == PROVIDER_AZURE_OPENAI:
            azure_ad_token = self._get_azure_ad_token()

        if azure_ad_token is not None:
            if headers.get("Authorization") is None:
                headers["Authorization"] = f"Bearer {azure_ad_token}"
        elif self.api_key:
            if headers.get("api-key") is None:
                headers["api-key"] = self.api_key
        else:
            # should never be hit
            raise ValueError("Unable to handle auth")

        return super()._prepare_options(options)
