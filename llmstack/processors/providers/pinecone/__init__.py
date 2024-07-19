from typing import Optional

from pydantic import BaseModel, Field

from llmstack.processors.providers.config import ProviderConfig


class APIKey(BaseModel):
    api_key: str = Field(
        title="API Key",
        description="API Key for the Weaviate instance",
        default="",
        json_schema_extra={"widget": "password"},
    )


class PineconeProviderConfig(ProviderConfig):
    api_key: Optional[APIKey] = Field(
        title="API Key",
        description="API Key for the Weaviate instance",
        default=None,
    )
    environment: Optional[str] = Field(
        title="Environment",
        description="Environment for the Weaviate instance",
        default=None,
    )
