import logging
import uuid
from typing import List

from datasources.handlers.datasource_type_interface import DataSourceEntryItem
from datasources.handlers.datasource_type_interface import DataSourceProcessor
from datasources.models import DataSource
from datasources.models import DataSourceEntry
from datasources.models import DataSourceEntryStatus
from datasources.types import DataSourceTypeFactory
import weaviate

logger = logging.getLogger(__name__)


def add_data_entry_task(datasource: DataSource, datasource_entry_items: List[DataSourceEntryItem]):
    logger.info(f'Adding data_source_entries')

    datasource_entry_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
        datasource.type,
    )
    datasource_entry_handler: DataSourceProcessor = datasource_entry_handler_cls(
        datasource,
    )

    datasource_entries_size = 0
    for datasource_entry_item in datasource_entry_items:
        datasource_entry_object = DataSourceEntry.objects.get(
            uuid=uuid.UUID(datasource_entry_item.uuid),
        )
        try:
            result = datasource_entry_handler.add_entry(datasource_entry_item)
            datasource_entry_object.config = result.config
            datasource_entry_object.size = result.size
            datasource_entry_object.status = DataSourceEntryStatus.READY
            datasource_entries_size += result.size
        except Exception as e:
            logger.exception(
                f'Error adding data_source_entry: %s' %
                str(datasource_entry_item.name),
            )
            datasource_entry_object.status = DataSourceEntryStatus.FAILED
            datasource_entry_object.config = {'errors': {'message': str(e)}}

        logger.debug(
            f'Updating data_source_entry: %s' %
            str(datasource_entry_item.uuid),
        )
        logger.debug(f'Status: %s' % str(datasource_entry_object.status))

        datasource_entry_object.save()

    datasource.size = datasource.size + datasource_entries_size
    datasource.save(update_fields=['size'])
    return datasource_entry_items


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
        entry_data.config = {'errors': {'message':"Error in deleting data source entry"}}
        entry_data.save()
    
    datasource.save()
    return datasource_entry_items


def delete_data_source_task(datasource):
    datasource_type = datasource.type
    datasource_entry_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
        datasource_type,
    )
    datasource_entry_handler = datasource_entry_handler_cls(datasource)
    datasource_entry_handler.delete_all_entries()
