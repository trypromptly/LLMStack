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
    base_url: str = Field(
        title="Base URL",
        description=(
            "Base URL for the MiniMax chat API. Use https://api.minimax.io/v1 or "
            "https://api.minimaxi.com/v1 for the OpenAI-compatible API. Use "
            "https://api.minimax.io/anthropic or https://api.minimaxi.com/anthropic "
            "for the Anthropic-compatible API."
        ),
        default="https://api.minimax.io/v1",
        min_length=1,
    )
