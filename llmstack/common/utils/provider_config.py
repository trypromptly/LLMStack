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
