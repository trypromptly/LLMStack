from typing import Optional

from pydantic import Field

from llmstack.processors.providers.config import ProviderConfig


class AzureProviderConfig(ProviderConfig):
    provider_slug: str = "azure"
    azure_endpoint: str = Field(
        title="Azure Endpoint",
        description="Azure Endpoint",
        default="",
        json_schema_extra={"advanced_parameter": False},
    )
    azure_deployment: str = Field(
        title="Azure Deployment",
        description="Azure Deployment",
        default="",
        json_schema_extra={"advanced_parameter": False},
    )
    api_version: str = Field(
        title="API Version",
        description="API Version",
        default="2023-05-15",
    )
    api_key: str = Field(
        title="API Key",
        description="API Key",
        default="",
        json_schema_extra={"widget": "password", "advanced_parameter": False},
    )
    organization: Optional[str] = Field(
        title="Organization",
        description="Organization ID to use in Azure API requests",
        default=None,
    )
