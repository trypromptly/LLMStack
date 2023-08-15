import logging

from .api_processor_interface import ApiProcessorInterface

logger = logging.getLogger(__name__)

class ApiProcessorFactory:
    """
    Factory class for API processors
    """
    @staticmethod
    def get_api_processor(api_backend_name) -> ApiProcessorInterface:
        subclasses = ApiProcessorInterface.__subclasses__()
        for subclass in subclasses:
            # Convert to lowercase to avoid case sensitivity
            if subclass.slug() == api_backend_name:
                return subclass
        return None
