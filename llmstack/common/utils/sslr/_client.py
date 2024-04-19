import json
import os
from enum import Enum
from typing import Any, List, Literal, Mapping, Optional, Type, Union, overload

import httpx
from openai import OpenAI
from openai._base_client import _StreamT
from openai._client import SyncAPIClient
from openai._models import FinalRequestOptions
from openai._utils import is_given
from openai.lib.azure import AzureADTokenProvider
from pydantic import BaseModel, Field
from typing_extensions import override

from ._exceptions import LLMError
from ._response import LLMResponse
from ._streaming import (
    AsyncStream,
    LLMAnthropicStream,
    LLMCohereStream,
    LLMGRPCStream,
    LLMRestStream,
)
from ._types import NOT_GIVEN, NotGiven, ResponseT, Timeout
from ._utils import LLMHttpResponse, is_mapping
from .constants import (
    DEFAULT_MAX_RETRIES,
    PROVIDER_ANTHROPIC,
    PROVIDER_AZURE_OPENAI,
    PROVIDER_COHERE,
    PROVIDER_CUSTOM,
    PROVIDER_GOOGLE,
    PROVIDER_LOCALAI,
    PROVIDER_MISTRAL,
    PROVIDER_OPENAI,
    PROVIDER_STABILITYAI,
)
from .resources import Audio, Chat, Completions, Embeddings, Images, Models


class ModelDeploymentProvider(str, Enum):
    HUGGINGFACE = "huggingface"
    GCP = "gcp"
    AZURE = "azure"
    AWS = "aws"

    def __str__(self):
        return self.value


class BearerAuthentication(BaseModel):
    _type: Literal["bearer_authentication"] = "bearer_authentication"
    bearer_token: str = Field(default="", description="The auth token to use.")


class DeploymentConfig(BaseModel):
    provider: ModelDeploymentProvider = Field(
        default=ModelDeploymentProvider.HUGGINGFACE,
        description="The provider of the Llama model.",
    )
    deployment_url: str = Field(
        default="",
        description="The URL of the deployed Llama model.",
    )
    credentials: Union[BearerAuthentication, None] = Field(
        description="The API key to use for the deployed model.",
    )
    model_name: Optional[str] = Field(
        default=None,
        description="The name of the model to use.",
    )

    @property
    def token(self):
        if self.credentials._type == "bearer_authentication":
            return self.credentials.bearer_token
        else:
            return None

    @property
    def base_url(self):
        return self.deployment_url


class LLMClient(SyncAPIClient):
    def _prepare_options(
        self,
        options: FinalRequestOptions,  # noqa: ARG002
    ) -> None:
        return super()._prepare_options(options)

    def _prepare_request(
        self,
        request: httpx.Request,  # noqa: ARG002
    ) -> None:
        return super()._prepare_request(request)

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

    def _process_response_data(
        self,
        *,
        data: object,
        cast_to: type[ResponseT],
        response: httpx.Response,
    ) -> ResponseT:
        return super()._process_response_data(data=data, cast_to=cast_to, response=response)

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

        elif self._llm_router_provider == PROVIDER_ANTHROPIC and response.request.url.path.endswith("/messages"):
            if not stream:
                json_response = response.json()
                result = {
                    "id": json_response["id"],
                    "object": "'chat.completion",
                    "created": 0,
                    "model": json_response["model"],
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": json_response["content"],
                            },
                            "finish_reason": json_response["stop_reason"],
                        }
                    ],
                    "usage": {
                        "prompt_tokens": json_response["usage"]["input_tokens"],
                        "completion_tokens": json_response["usage"]["output_tokens"],
                        "total_tokens": json_response["usage"]["input_tokens"]
                        + json_response["usage"]["output_tokens"],
                    },
                }
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
        elif self._llm_router_provider == PROVIDER_COHERE and response.request.url.path.endswith("/chat"):
            if not stream:
                json_response = response.json()
                request_data = json.loads(response.request._content.decode("utf-8"))
                try:
                    input_tokens = json_response["meta"]["tokens"]["input_tokens"]
                    output_tokens = json_response["meta"]["tokens"]["output_tokens"]
                    total_tokens = input_tokens + output_tokens
                except Exception:
                    input_tokens = None
                    output_tokens = None
                    total_tokens = None
                result = {
                    "id": json_response["generation_id"],
                    "object": "'chat.completion",
                    "created": 0,
                    "model": request_data["model"],
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": json_response["text"],
                            },
                            "finish_reason": json_response["finish_reason"],
                        }
                    ],
                    "usage": {
                        "prompt_tokens": input_tokens,
                        "completion_tokens": output_tokens,
                        "total_tokens": total_tokens,
                    },
                }
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

    def _request(
        self,
        *,
        cast_to: Type[ResponseT],
        options: FinalRequestOptions,
        remaining_retries: int | None,
        stream: bool,
        stream_cls: type[_StreamT] | None,
    ) -> ResponseT | _StreamT:
        return super()._request(
            cast_to=cast_to,
            options=options,
            remaining_retries=remaining_retries,
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

    # Mistral options
    @overload
    def __init__(
        self,
        *,
        provider: Literal["mistral"],
        mistral_api_key: str,
        base_url: str,
        organization: Optional[str] = None,
        timeout: Union[float, Timeout, None, NotGiven] = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Optional[Mapping[str, str]] = None,
        default_query: Optional[Mapping[str, object]] = None,
        http_client: Optional[httpx.Client] = None,
        _strict_response_validation: bool = False,
    ) -> None:
        ...

    # Custom model deployments
    @overload
    def __init__(
        self,
        *,
        provider: Literal["custom"],
        deployment_configs: List[DeploymentConfig],
        timeout: Union[float, Timeout, None, NotGiven] = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Optional[Mapping[str, str]] = None,
        default_query: Optional[Mapping[str, object]] = None,
        http_client: Optional[httpx.Client] = None,
        _strict_response_validation: bool = False,
    ) -> None:
        ...

    # Anthropic options
    @overload
    def __init__(
        self,
        *,
        anthropic_api_key: str,
        base_url: str,
        organization: Optional[str] = None,
        timeout: Union[float, Timeout, None, NotGiven] = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Optional[Mapping[str, str]] = None,
        default_query: Optional[Mapping[str, object]] = None,
        http_client: Optional[httpx.Client] = None,
        _strict_response_validation: bool = False,
    ) -> None:
        ...

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

    # Cohere options
    @overload
    def __init__(
        self,
        *,
        cohere_api_key: str,
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
        cohere_api_key: Optional[str] = None,
        api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        localai_api_key: Optional[str] = None,
        azure_api_key: Optional[str] = None,
        google_api_key: Optional[str] = None,
        stabilityai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        azure_ad_token: Optional[str] = None,
        azure_ad_token_provider: Optional[AzureADTokenProvider] = None,
        mistral_api_key: Optional[str] = None,
        deployment_configs: List[DeploymentConfig],
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

        elif provider == PROVIDER_ANTHROPIC:
            api_key = anthropic_api_key
            self.auth_token = None
            if base_url is None:
                base_url = "https://api.anthropic.com/v1"

        elif provider == PROVIDER_COHERE:
            api_key = cohere_api_key
            if base_url is None:
                base_url = "https://api.cohere.ai/v1"

        elif provider == PROVIDER_MISTRAL:
            api_key = mistral_api_key
            if base_url is None:
                base_url = "https://api.mistral.ai/v1"

        elif provider == PROVIDER_CUSTOM:
            if not deployment_configs:
                raise ValueError("deployment_config is required for custom provider")
            self.deployment_configs = deployment_configs
            api_key = deployment_configs[0].token
            base_url = deployment_configs[0].base_url

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
        elif provider == PROVIDER_ANTHROPIC:
            self._default_stream_cls = LLMAnthropicStream
        elif provider == PROVIDER_COHERE:
            self._default_stream_cls = LLMCohereStream

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

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        if self._llm_router_provider == PROVIDER_ANTHROPIC:
            if self.api_key:
                return {"X-Api-Key": self.api_key}
            if self.auth_token:
                return {"Authorization": f"Bearer {self.auth_token}"}

        api_key = self.api_key
        return {"Authorization": f"Bearer {api_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str]:
        headers = {
            **super().default_headers,
            "X-Stainless-Async": "false",
        }
        if self._llm_router_provider == PROVIDER_OPENAI:
            headers["OpenAI-Organization"] = self.organization if self.organization is not None else ""

        headers = {**headers, **self._custom_headers}

        if self._llm_router_provider == PROVIDER_ANTHROPIC:
            headers["anthropic-version"] = "2023-06-01"

        return headers
