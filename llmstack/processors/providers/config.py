from enum import Enum
from typing import Dict

from pydantic import ConfigDict, Field

from llmstack.base.billing import BaseBillingMetric
from llmstack.common.blocks.base.schema import BaseSchema, CustomGenerateJsonSchema


class ProviderConfigSource(str, Enum):
    """
    Provider configuration source
    """

    PROFILE = "profile"
    PLATFORM_DEFAULT = "platform_default"
    ORGANIZATION = "organization"

    def __str__(self) -> str:
        return self.value


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

    def get_billing_metrics(
        self, provider_slug=None, processor_slug=None, model_slug=None, deployment_name=None
    ) -> Dict[str, BaseBillingMetric]:
        import importlib

        from django.conf import settings

        get_pricing_data = getattr(importlib.import_module(settings.BILLING_MODULE), "get_pricing_data")

        pricing_provider_slug = provider_slug or self.provider_slug
        pricing_processor_slug = processor_slug or self.processor_slug
        pricing_model_slug = model_slug or self.model_slug
        pricing_deployment_name = deployment_name or self.deployment_key

        pricing_metrics = get_pricing_data(
            pricing_provider_slug,
            pricing_processor_slug,
            pricing_model_slug,
            pricing_deployment_name,
        )
        return {
            **pricing_metrics,
            "provider_slug": pricing_provider_slug,
            "processor_slug": pricing_processor_slug,
            "model_slug": pricing_model_slug,
            "deployment_key": pricing_deployment_name,
            "provider_config_source": str(self.provider_config_source),
        }
