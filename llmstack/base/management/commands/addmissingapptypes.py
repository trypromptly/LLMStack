import logging

from django.core.management.base import BaseCommand

from llmstack.apps.types.app_type_interface import AppTypeInterface

logger = logging.getLogger(__name__)


def add_missing_app_types():
    from llmstack.apps.types.agent import Agent  # noqa F401
    from llmstack.apps.types.chat import ChatApp  # noqa F401
    from llmstack.apps.types.web import WebApp  # noqa F401

    app_types = []
    for subclass in AppTypeInterface.__subclasses__():
        try:
            app_types.append(
                {
                    "slug": subclass.slug(),
                    "name": subclass.name(),
                    "description": subclass.description(),
                },
            )
        except Exception:
            logger.error(
                f"Error while loading app type: {subclass.slug()}",
            )
            pass

    # If app slug is already present, do not add it again
    from llmstack.apps.models import AppType

    for app_type in app_types:
        if AppType.objects.filter(slug=app_type["slug"]).exists():
            continue
        AppType.objects.create(**app_type)
        logger.info(f"Added App Type: {app_type['slug']}")


class Command(BaseCommand):
    help = "Add missing app types."

    def handle(self, *args, **options):
        add_missing_app_types()
