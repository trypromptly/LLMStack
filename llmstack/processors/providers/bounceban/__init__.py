from pydantic import Field

from llmstack.processors.providers.config import ProviderConfig


class BouncebanProviderConfig(ProviderConfig):
    provider_slug: str = "bounceban"
    api_key: str = Field(
        title="API Key",
        default="",
        description="API Key for the BounceBan API",
        json_schema_extra={"widget": "password", "advanced_parameter": False},
    )
