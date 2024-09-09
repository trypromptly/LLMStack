from pydantic import Field

from llmstack.processors.providers.config import ProviderConfig


class ApolloProviderConfig(ProviderConfig):
    provider_slug: str = "apollo"
    api_key: str = Field(
        title="API Key",
        default="",
        description="API Key for the Apollo API",
        json_schema_extra={"widget": "password", "advanced_parameter": False},
    )
