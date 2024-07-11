from typing import Optional

from pydantic import Field

from llmstack.processors.providers.config import ProviderConfig


class AnthropicProviderConfig(ProviderConfig):
    provider_slug: str = "anthropic"
    base_url: str = Field(
        title="Base URL",
        description="Base URL Anthropic API",
        default="https://api.anthropic.com/v1/",
    )
    api_key: str = Field(
        title="API Key",
        default="",
        description="API Key for the Anthropic API",
        json_schema_extra={"widget": "password", "advanced_parameter": False},
    )
    organization: Optional[str] = Field(
        title="Organization ID",
        default=None,
        description="Organization ID to use in Anthropic API requests",
    )
