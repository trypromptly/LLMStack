from pydantic import ConfigDict, Field

from llmstack.common.blocks.base.schema import (
    BaseSchema,
    CustomGenerateJsonSchema,
    StrEnum,
)


class ProviderConfigSource(StrEnum):
    """
    Provider configuration source
    """

    PROFILE = "profile"
    PLATFORM_DEFAULT = "platform_default"
    ORGANIZATION = "organization"


class ProviderConfig(BaseSchema):
    model_config = ConfigDict(protected_namespaces=())

    provider_slug: str = Field(
        title="Provider Slug",
        description="Provider slug",
        json_schema_extra={"widget": "hidden"},
    )
    processor_slug: str = Field(
        title="Processor Slug",
        description="Processor slug this provider configuration is associated with",
        default="*",
    )
    model_slug: str = Field(
        title="Model Slug",
        description="Unique slug for the model if applicable",
        default="*",
    )
    deployment_key: str = Field(
        title="Deployment Key",
        description="Unique key for the deployment configuration",
        default="*",
        json_schema_extra={"widget": "hidden"},
    )
    provider_config_source: ProviderConfigSource = Field(
        title="Provider Configuration Source",
        description="Source of the provider configuration",
        default=ProviderConfigSource.PROFILE,
        json_schema_extra={"widget": "hidden"},
    )

    def __str__(self) -> str:
        return f"{self.provider_slug}/{self.processor_slug}/{self.model_slug}/{self.deployment_key}"

    @classmethod
    def get_config_schema(cls):
        schema = cls.model_json_schema(schema_generator=CustomGenerateJsonSchema)

        if "description" in schema:
            schema.pop("description")
        if "title" in schema:
            schema.pop("title")
        if "properties" in schema and "provider_slug" in schema["properties"]:
            schema["properties"].pop("provider_slug")
        return schema

    @classmethod
    def get_config_ui_schema(cls) -> dict:
        return cls.get_ui_schema()
