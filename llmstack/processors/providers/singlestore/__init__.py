from pydantic import Field

from llmstack.processors.providers.config import ProviderConfig


class SinglestoreProviderConfig(ProviderConfig):
    provider_slug: str = "singlestore"

    host: str = Field(
        title="Database Host",
        description="Hostname of the SingleStore database",
        default="",
    )

    port: int = Field(
        title="Database Port",
        description="Port of the SingleStore database",
        default=3306,
    )

    username: str = Field(
        title="Database Username",
        description="Username for the SingleStore database",
        default="",
    )

    password: str = Field(
        title="Database Password",
        description="Password for the SingleStore database",
        default="",
        json_schema_extra={"widget": "password"},
    )
