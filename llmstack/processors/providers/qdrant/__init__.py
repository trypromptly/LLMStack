from typing import Optional

from pydantic import BaseModel, Field

from llmstack.processors.providers.config import ProviderConfig


class APIKey(BaseModel):
    api_key: str = Field(
        title="API Key",
        description="API Key for the Qdrant instance",
        default="",
        json_schema_extra={"widget": "password"},
    )


class QdrantProviderConfig(ProviderConfig):
    location: Optional[str] = Field(
        title="Location",
        description="Location for the Qdrant instance",
        default=None,
    )
    url: Optional[str] = Field(
        title="URL",
        description="URL for the Qdrant instance",
        default=None,
    )
    port: Optional[int] = Field(
        title="Port",
        description="Port for the Qdrant instance",
        default=None,
    )
    grpc_port: Optional[int] = Field(
        title="GRPC Port",
        description="GRPC Port for the Qdrant instance",
        default=None,
    )
    auth: Optional[APIKey] = Field(
        title="Auth",
        description="Auth for the Qdrant instance",
        default=None,
    )
