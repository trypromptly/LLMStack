import logging
import uuid
from typing import List

from llmstack.datasources.handlers.datasource_processor import DataSourceEntryItem
from llmstack.datasources.handlers.datasource_processor import DataSourceProcessor
from llmstack.datasources.models import DataSource
from llmstack.datasources.models import DataSourceEntry
from llmstack.datasources.models import DataSourceEntryStatus
from llmstack.datasources.types import DataSourceTypeFactory
import weaviate

logger = logging.getLogger(__name__)


def delete_data_entry_task(datasource: DataSource, entry_data: DataSourceEntry):
    logger.error(f'Deleting data_source_entry: %s' % str(entry_data.uuid))
    entry_data.status = DataSourceEntryStatus.MARKED_FOR_DELETION
    entry_data.save()

    datasource.size -= entry_data.size
    datasource_entry_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
        datasource.type,
    )
    datasource_entry_handler = datasource_entry_handler_cls(datasource)
    try:
        datasource_entry_items = datasource_entry_handler.delete_entry(
            entry_data.config,
        )
        entry_data.delete()
    except weaviate.exceptions.UnexpectedStatusCodeException:
        logger.exception("Error deleting data source entry from weaviate")
        entry_data.delete()
    except Exception as e:
        logger.exception(
            f'Error deleting data_source_entry: %s' %
            str(entry_data.name),
        )
        entry_data.status = DataSourceEntryStatus.FAILED
        entry_data.config = {'errors': {
            'message': "Error in deleting data source entry"}}
        entry_data.save()

    datasource.save()
    return


def resync_data_entry_task(datasource: DataSource, entry_data: DataSourceEntry):
    logger.info(f'Resyncing task for data_source_entry: %s' % str(entry_data))

    datasource_entry_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
        datasource.type,
    )
    datasource_entry_handler: DataSourceProcessor = datasource_entry_handler_cls(
        datasource,
    )
    entry_data.status = DataSourceEntryStatus.PROCESSING
    entry_data.save()
    old_size = entry_data.size

    result = datasource_entry_handler.resync_entry(entry_data.config)
    entry_data.size = result.size
    config_entry = result.config
    config_entry["input"] = entry_data.config["input"]
    entry_data.config = config_entry
    entry_data.status = DataSourceEntryStatus.READY
    entry_data.save()

    datasource.size = datasource.size - old_size + result.size
    datasource.save()


def delete_data_source_task(datasource):
    datasource_type = datasource.type
    if datasource_type.is_external_datasource:
        return
    datasource_entry_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
        datasource_type,
    )
    datasource_entry_handler = datasource_entry_handler_cls(datasource)
    datasource_entry_handler.delete_all_entries()
