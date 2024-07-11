from pydantic import Field

from llmstack.processors.providers.config import ProviderConfig


class CohereProviderConfig(ProviderConfig):
    provider_slug: str = "cohere"
    api_key: str = Field(
        title="API Key",
        description="Your Cohere API Key",
        default="",
        json_schema_extra={"widget": "password", "advanced_parameter": False},
    )
