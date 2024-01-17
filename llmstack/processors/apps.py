import logging

from django.apps import AppConfig
from django.conf import settings

from llmstack.common.utils.module_loader import get_all_sub_classes

from .providers.api_processor_interface import ApiProcessorInterface

logger = logging.getLogger(__name__)


def load_processor_subclasses():
    subclasses = ApiProcessorInterface.__subclasses__()
    allowed_packages = settings.PROCESSOR_PROVIDERS
    for package in allowed_packages:
        subclasses.extend(get_all_sub_classes(package, ApiProcessorInterface))


class ProcessorsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "llmstack.processors"
    label = "apiabstractor"

    def ready(self) -> None:
        from sys import argv

        # If this is collecstatic command, do not load the processor subclasses
        if "collectstatic" in argv:
            return
        logger.info("Initializing Processor subclasses")
        load_processor_subclasses()
