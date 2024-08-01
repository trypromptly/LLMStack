from enum import Enum
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field

from llmstack.common.utils.sslr._client import LLM
from llmstack.processors.providers.config import ProviderConfig
from llmstack.processors.providers.google import get_google_credentials_from_json_key


class ContentMimeType(str, Enum):
    TEXT = "text/plain"
    JSON = "application/json"
    HTML = "text/html"
    PNG = "image/png"
    JPEG = "image/jpeg"
    SVG = "image/svg+xml"
    PDF = "application/pdf"
    LATEX = "application/x-latex"

    def __str__(self):
        return self.value


class Content(BaseModel):
    data: str = Field(description="The content data")
    mime_type: ContentMimeType = Field(description="The content mime type", default=ContentMimeType.TEXT)


class GoogleSearchEngineConfig(BaseModel):
    type: Literal["google"] = "google"
    api_key: str = Field(
        title="Google Custom Search API Key",
        description="API Key for Google Custom Search API",
        default="",
        json_schema_extra={"widget": "password", "advanced_parameter": False},
    )
    cx: str = Field(
        title="Google Custom Search Engine ID",
        description="Custom Search Engine ID for Google Custom Search API",
        default="",
        json_schema_extra={"advanced_parameter": False},
    )


SearchEngineConfig = Union[GoogleSearchEngineConfig]


class EmbeddingsGeneratorConfig(BaseModel):
    provider_slug: Optional[str] = Field(
        title="Embeddings Provider slug",
        description="Embeddings Provider slug",
        default="openai",
    )
    embedding_model_slug: Optional[str] = Field(
        title="Embeddings Provider Model",
        description="Embeddings Provider Model",
        default="text-embedding-ada-002",
    )


class DataDestinationConfig(BaseModel):
    provider_slug: Optional[str] = Field(
        title="Data Destination Provider slug",
        description="Data Destination Provider slug",
        default="weaviate",
    )
    processor_slug: Optional[str] = Field(
        title="Data Destination Processor slug",
        description="Data Destination Processor slug",
        default="vector-store",
    )
    additional_kwargs: Optional[dict] = Field(
        title="Additional Keyword Arguments",
        description="Additional Keyword Arguments",
        default={},
    )


class PromptlyProviderConfig(ProviderConfig):
    provider_slug: str = "promptly"
    search_engine: Optional[SearchEngineConfig] = Field(
        title="Search Engine",
        description="Search Engine Configuration",
        default=None,
    )
    embeddings_generator: Optional[EmbeddingsGeneratorConfig] = Field(
        title="Embeddings Generator",
        description="Embeddings Generator Configuration",
        default=None,
    )
    data_destination_configuration: Optional[DataDestinationConfig] = Field(
        title="Default Data Destination Configuration",
        description="Default Data Destination Configuration",
        default=None,
    )


def get_llm_client_from_provider_config(provider, model_slug, get_provider_config_fn):
    try:
        google_provider_config = get_provider_config_fn(
            provider_slug="google",
            model_slug=model_slug,
        )
    except Exception:
        google_provider_config = None

    try:
        openai_provider_config = get_provider_config_fn(
            provider_slug="openai",
            model_slug=model_slug,
        )
    except Exception:
        openai_provider_config = None

    try:
        stability_provider_config = get_provider_config_fn(
            provider_slug="stabilityai",
            model_slug=model_slug,
        )
    except Exception:
        stability_provider_config = None

    try:
        anthropic_provider_config = get_provider_config_fn(
            provider_slug="anthropic",
            model_slug=model_slug,
        )
    except Exception:
        anthropic_provider_config = None

    try:
        cohere_provider_config = get_provider_config_fn(
            provider_slug="cohere",
            model_slug=model_slug,
        )
    except Exception:
        cohere_provider_config = None

    google_api_key, token_type = (
        get_google_credentials_from_json_key(google_provider_config.service_account_json_key)
        if google_provider_config
        else (None, None)
    )

    return LLM(
        provider=provider,
        openai_api_key=openai_provider_config.api_key if openai_provider_config else "",
        stabilityai_api_key=stability_provider_config.api_key if stability_provider_config else "",
        google_api_key=google_api_key if google_api_key else "",
        anthropic_api_key=anthropic_provider_config.api_key if anthropic_provider_config else "",
        cohere_api_key=cohere_provider_config.api_key if cohere_provider_config else "",
    )
