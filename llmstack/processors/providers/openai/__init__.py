from typing import Optional

from pydantic import Field

from llmstack.processors.providers.config import ProviderConfig


class OpenAIProviderConfig(ProviderConfig):
    provider_slug: str = "openai"
    base_url: str = Field(
        title="Base URL",
        description="Base URL for the OpenAI API. Use any OpenAI compatible API URL.",
        default="https://api.openai.com/v1/",
    )

    api_key: str = Field(
        title="API Key",
        default="",
        description="API Key for the OpenAI API",
        json_schema_extra={"widget": "password", "advanced_parameter": False},
    )

    organization_id: Optional[str] = Field(
        title="Organization ID",
        default=None,
        description="Organization ID to use in OpenAI API requests",
    )
