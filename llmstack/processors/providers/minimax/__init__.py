from typing import Literal

from pydantic import Field

from llmstack.processors.providers.config import ProviderConfig


class MiniMaxProviderConfig(ProviderConfig):
    provider_slug: str = "minimax"
    api_key: str = Field(
        title="API Key",
        description="Your MiniMax API key.",
        default="",
        json_schema_extra={"widget": "password", "advanced_parameter": False},
    )
    speech_api_url: Literal["https://api.minimax.io/v1/t2a_v2", "https://api.minimaxi.com/v1/t2a_v2"] = Field(
        default="https://api.minimax.io/v1/t2a_v2",
        title="Speech API URL",
        description="Use the endpoint for the region of your MiniMax account.",
        json_schema_extra={"advanced_parameter": False},
    )
