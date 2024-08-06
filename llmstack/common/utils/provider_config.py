import sys
from functools import cache
from importlib import import_module

from django.conf import settings


@cache
def get_provider_config_classes_cached():
    # Returns a list of tuples of provider slug and provider config class
    processor_providers = list(
        filter(
            lambda provider: provider.get(
                "config_schema",
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
        import_module(".".join(provider.get("config_schema").rsplit(".", 1)[:-1]))

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


def get_matched_provider_config(
    provider_configs={}, provider_slug="*", processor_slug="*", model_slug="*", deployment_key="*"
):
    """
    Finds the provider config schema class and get the
    """
    provider_config_cls = get_provider_config_class_by_slug_cached(provider_slug)
    provider_config_key = f"{provider_slug}/{processor_slug}/{model_slug}/{deployment_key}"

    if not provider_config_cls or not provider_configs:
        raise Exception(f"Configuration for this provider doesn't exist: {provider_slug}")

    # Get all the provider config keys for this provider
    config_keys_with_parts = list(map(lambda key: (key, key.split("/")), provider_configs.keys()))
    config_keys_with_parts = list(filter(lambda key: key[1][0] == provider_slug, config_keys_with_parts))

    # Filter config_keys that the processor slug matches the regex in the config key split 1
    config_keys_with_parts = list(
        filter(lambda key: key[1][1] == "*" or key[1][1] == processor_slug, config_keys_with_parts)
    )

    # Filter config_keys that the model slug matches the regex in the config key split 2
    config_keys_with_parts = list(
        filter(lambda key: key[1][2] == "*" or key[1][2] == model_slug, config_keys_with_parts)
    )

    # Filter config_keys that the deployment key matches the regex in the config key split 3
    config_keys_with_parts = list(
        filter(lambda key: key[1][3] == "*" or key[1][3] == deployment_key, config_keys_with_parts)
    )

    # Sort the remaning config keys by the number of * in the key in descending order and we take the first one
    config_key = (
        sorted(config_keys_with_parts, key=lambda key: key[1].count("*"))[0][0]
        if len(config_keys_with_parts) > 0
        else None
    )

    if not config_key:
        raise Exception(f"Configuration for this provider doesn't exist: {provider_config_key}")

    return provider_config_cls(**provider_configs[config_key])
