import logging

import weaviate

from llmstack.data.models import DataSource, DataSourceEntry, DataSourceEntryStatus
from llmstack.data.sources.datasource_processor import DataSourceProcessor
from llmstack.data.types import DataSourceTypeFactory

logger = logging.getLogger(__name__)


def delete_data_entry_task(
    datasource: DataSource,
    entry_data: DataSourceEntry,
):
    logger.error("Deleting data_source_entry: %s" % str(entry_data.uuid))
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
        if datasource_entry_items:
            logger.debug(
                f"Deleted {len(datasource_entry_items)} items from weaviate for data_source_entry: {str(entry_data.uuid)}",
            )
        entry_data.delete()
    except weaviate.exceptions.UnexpectedStatusCodeException:
        logger.exception("Error deleting data source entry from weaviate")
        entry_data.delete()
    except Exception:
        logger.exception(
            "Error deleting data_source_entry: %s" % str(entry_data.name),
        )
        entry_data.status = DataSourceEntryStatus.FAILED
        entry_data.config = {
            "errors": {
                "message": "Error in deleting data source entry",
            },
        }
        entry_data.save()

    datasource.save()
    return


def resync_data_entry_task(
    datasource: DataSource,
    entry_data: DataSourceEntry,
):
    logger.info("Resyncing task for data_source_entry: %s" % str(entry_data))

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
