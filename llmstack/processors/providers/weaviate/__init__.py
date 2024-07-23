from enum import Enum
from typing import Annotated, List, Optional, Union

from pydantic import BaseModel, Field

from llmstack.processors.providers.config import ProviderConfig


class APIKey(BaseModel):
    api_key: str = Field(
        title="API Key",
        description="API Key for the Weaviate instance",
        default="",
        json_schema_extra={"widget": "password"},
    )


class BasicAuthentication(BaseModel):
    username: str = Field(
        title="Username",
        description="Username for the Weaviate instance",
        default="",
    )
    password: str = Field(
        title="Password",
        description="Password for the Weaviate instance",
        default="",
        json_schema_extra={"widget": "password"},
    )


class Header(BaseModel):
    key: str = Field(
        title="Header Key",
        description="Key for the header",
        default="",
    )
    value: str = Field(
        title="Header Value",
        description="Value for the header",
        default="",
    )


AuthType = Annotated[Union[APIKey, BasicAuthentication], Field(title="Authentication Type")]


class WeaviateLocalInstance(BaseModel):
    url: Optional[str] = Field(title="Weaviate URL", description="URL of the Weaviate instance", default="")
    http_host: Optional[str] = Field(title="HTTP Host", description="HTTP Host of the Weaviate instance", default="")
    http_port: Optional[int] = Field(title="HTTP Port", description="HTTP Port of the Weaviate instance", default=0)
    http_secure: Optional[bool] = Field(
        title="HTTP Secure", description="HTTP Secure of the Weaviate instance", default=False
    )
    grpc_host: Optional[str] = Field(title="GRPC Host", description="GRPC Host of the Weaviate instance", default="")
    grpc_port: Optional[int] = Field(title="GRPC Port", description="GRPC Port of the Weaviate instance", default=0)
    grpc_secure: Optional[bool] = Field(
        title="GRPC Secure", description="GRPC Secure of the Weaviate instance", default=False
    )


class EmbeddingsProvider(str, Enum):
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"

    def __str__(self):
        return str(self.value)


class WeaviateCloudInstance(BaseModel):
    cluster_url: Optional[str] = Field(title="Cluster URL", description="URL of the Weaviate cluster", default="")


class WeaviateProviderConfig(ProviderConfig):
    instance: Union[WeaviateLocalInstance, WeaviateCloudInstance] = Field(
        title="Weaviate Instance Configuration",
        description="Weaviate instance configuration",
    )
    auth: Optional[AuthType] = Field(title="Authentication", description="Authentication for the Weaviate instance")
    additional_headers: Optional[List[Header]] = Field(
        title="Additional Headers",
        description="Additional headers for the Weaviate instance",
        default=[],
    )
    embeddings_provider: Optional[EmbeddingsProvider] = Field(
        title="Embeddings Provider",
        description="Embeddings provider for the Weaviate instance",
        default=None,
    )
    module_config: Optional[str] = Field(
        title="Module Configuration JSON",
        description="Module configuration for the Weaviate instance",
        default="",
    )

    @property
    def additional_headers_dict(self):
        return {header.key: header.value for header in self.additional_headers}
