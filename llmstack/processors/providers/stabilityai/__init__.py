from typing import Optional

from pydantic import Field

from llmstack.processors.providers.config import ProviderConfig


class StabilityAIProviderConfig(ProviderConfig):
    provider_slug: str = "stabilityai"
    api_key: str = Field(
        title="API Key",
        description="Your Stability AI API Key",
        default="",
        json_schema_extra={"widget": "password", "advanced_parameter": False},
    )
    base_url: Optional[str] = Field(
        title="Base URL",
        description="Base URL for the Stability AI API.",
        default=None,
    )
    organization: Optional[str] = Field(
        title="Organization ID",
        description="Organization ID to use in Stability AI API requests",
        default=None,
    )
    client_id: Optional[str] = Field(
        title="Client ID",
        description="Client ID to use in Stability AI API requests",
        default=None,
    )
    client_version: Optional[str] = Field(
        title="Client Version",
        description="Client Version to use in Stability AI API requests",
        default=None,
    )
