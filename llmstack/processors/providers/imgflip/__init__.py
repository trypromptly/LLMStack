from pydantic import Field

from llmstack.processors.providers.config import ProviderConfig


class ImgFlipProviderConfig(ProviderConfig):
    provider_slug: str = "imgflip"
    username: str = Field(
        title="Username",
        default="",
        description="Username for the ImgFlip API",
        json_schema_extra={"widget": "text", "advanced_parameter": False},
    )
    password: str = Field(
        title="Password",
        default="",
        description="Password for the ImgFlip API",
        json_schema_extra={"widget": "password", "advanced_parameter": False},
    )
