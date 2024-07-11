import sys
from functools import cache

from django.conf import settings


@cache
def get_provider_config_classes_cached():
    # Returns a list of tuples of provider slug and provider config class
    processor_providers = list(
        filter(
            lambda provider: provider.get(
                "processor_packages",
            ),
            settings.PROVIDERS,
        ),
    )

    provider_classes = []
    for provider in filter(
        lambda provider: provider.get(
            "config_schema",
        ),
        processor_providers,
    ):
        provider_classes.append(
            (
                provider.get("slug"),
                getattr(
                    sys.modules[".".join(provider.get("config_schema").rsplit(".", 1)[:-1])],
                    provider.get("config_schema").split(".")[-1],
                ),
            ),
        )

    return provider_classes


@cache
def get_provider_config_class_by_slug_cached(provider_slug: str):
    provider_classes = get_provider_config_classes_cached()
    for provider in provider_classes:
        if provider[0] == provider_slug:
            return provider[1]
    return None


def validate_provider_configs(provider_configs):
    # Iterate through the provider configs, validate them against the schema and encrypt the values
    for provider_key, provider_config in provider_configs.items():
        if not provider_config:
            continue

        # provider_key is of the form provider_slug/processor_slug/model_slug/deployment_key where processor_slug and model_slug can be regex
        provider_key_parts = provider_key.split("/")
        [provider_slug, processor_slug, model_slug, deployment_key] = provider_key_parts

        # Get schema class for the provider
        provider_schema_cls = get_provider_config_class_by_slug_cached(provider_slug)
        if not provider_schema_cls:
            raise Exception(f"Provider schema class not found for {provider_slug}")

        # Validate the key against the schema
        if (
            provider_slug != provider_config["provider_slug"]
            or processor_slug != provider_config["processor_slug"]
            or model_slug != provider_config["model_slug"]
            or deployment_key != provider_config["deployment_key"]
        ):
            raise Exception(f"Provider config key {provider_key} does not match the schema")

        # Validate the config against the schema
        provider_schema_cls.model_validate(provider_config)
