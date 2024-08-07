from typing import Optional

from pydantic import BaseModel, Field

from llmstack.processors.providers.config import ProviderConfig


class APIKey(BaseModel):
    api_key: str = Field(
        title="API Key",
        description="API Key for the Pinecone instance",
        default="",
        json_schema_extra={"widget": "password"},
    )


class PineconeProviderConfig(ProviderConfig):
    auth: Optional[APIKey] = Field(
        title="Auth",
        description="Auth for the Pinecone instance",
        default=None,
    )
    environment: Optional[str] = Field(
        title="Environment",
        description="Environment for the Pinecone instance",
        default=None,
    )
