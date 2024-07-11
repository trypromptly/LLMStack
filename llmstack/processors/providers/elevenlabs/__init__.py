from pydantic import Field

from llmstack.processors.providers.config import ProviderConfig


class ElevenLabsProviderConfig(ProviderConfig):
    provider_slug: str = "elevenlabs"
    api_key: str = Field(
        title="API Key",
        description="Your Eleven Labs API Key",
        default="",
        json_schema_extra={"widget": "password", "advanced_parameter": False},
    )
    base_url: str = Field(
        title="Base URL",
        description="Base URL for the Eleven Labs API.",
        default="https://api.elevenlabs.io/v1/",
    )
