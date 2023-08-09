from functools import lru_cache

from django.conf import settings

from .handlers.datasource_type_interface import DataSourceTypeInterface
from .models import DataSourceType
# Import all data source types here

from common.utils.module_loader import get_all_sub_classes


def get_data_source_type_interface_subclasses():
    subclasses = DataSourceTypeInterface.__subclasses__()
    allowed_packages = settings.DATASOURCE_TYPE_PROVIDERS

    for package in allowed_packages:
        subclasses.extend(get_all_sub_classes(
            package, DataSourceTypeInterface))

    return subclasses


class DataSourceTypeFactory:
    """
    Factory class for Data source types
    """
    @staticmethod
    def get_datasource_type_handler(datasource_type: DataSourceType) -> DataSourceTypeInterface:
        subclasses = get_data_source_type_interface_subclasses()
        for subclass in subclasses:
            # Convert to lowercase to avoid case sensitivity
            if subclass.slug() == datasource_type.slug.lower():
                return subclass
        return None
