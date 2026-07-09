from typing import Optional

from pydantic import Field

from llmstack.processors.providers.config import ProviderConfig


class MiniMaxProviderConfig(ProviderConfig):
    provider_slug: str = "minimax"
    api_key: str = Field(
        title="API Key",
        description="Your MiniMax API Key",
        default="",
        json_schema_extra={"widget": "password", "advanced_parameter": False},
    )
    base_url: Optional[str] = Field(
        title="Base URL",
        description="Base URL for the MiniMax OpenAI-compatible API.",
        default="https://api.minimax.io/v1",
    )
    organization: Optional[str] = Field(
        title="Organization ID",
        description="Organization ID to use in MiniMax API requests",
        default=None,
    )
