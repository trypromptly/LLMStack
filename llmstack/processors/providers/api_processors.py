import logging

from .api_processor_interface import ApiProcessorInterface

logger = logging.getLogger(__name__)


class ApiProcessorFactory:
    """
    Factory class for API processors
    """

    @staticmethod
    def get_api_processor(
        processor_slug,
        provider_slug=None,
    ) -> ApiProcessorInterface:
        processor_slug = processor_slug.split("/")[0]

        subclasses = ApiProcessorInterface.__subclasses__()
        for subclass in subclasses:
            # Convert to lowercase to avoid case sensitivity
            if subclass.slug() == processor_slug and subclass.provider_slug() == provider_slug:
                return subclass
        return None
