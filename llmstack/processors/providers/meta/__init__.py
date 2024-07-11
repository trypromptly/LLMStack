from pydantic import Field

from llmstack.common.utils.sslr._client import DeploymentConfig
from llmstack.processors.providers.config import ProviderConfig


class MetaProviderConfig(ProviderConfig):
    provider_slug: str = "meta"
    deployment_config: DeploymentConfig = Field(
        title="Deployment Config",
        description="Deployment Config",
        json_schema_extra={"advanced_parameter": False},
    )
