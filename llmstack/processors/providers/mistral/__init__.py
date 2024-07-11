from typing import Optional

from pydantic import Field

from llmstack.processors.providers.config import ProviderConfig


class MistralProviderConfig(ProviderConfig):
    provider_slug: str = "mistral"
    api_key: str = Field(
        title="API Key",
        description="Your Mistral API Key",
        default="",
        json_schema_extra={"widget": "password", "advanced_parameter": False},
    )
    base_url: Optional[str] = Field(
        title="Base URL",
        description="Base URL for the Mistral API.",
        default=None,
    )
    organization: Optional[str] = Field(
        title="Organization ID",
        description="Organization ID to use in Mistral API requests",
        default=None,
    )
