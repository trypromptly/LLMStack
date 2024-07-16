import logging

from llmstack.data.datasource_processor import DataPipeline
from llmstack.data.models import DataSource, DataSourceEntry, DataSourceEntryStatus
from llmstack.data.types import DataSourceTypeFactory

logger = logging.getLogger(__name__)


def resync_data_entry_task(
    datasource: DataSource,
    entry_data: DataSourceEntry,
):
    logger.info("Resyncing task for data_source_entry: %s" % str(entry_data))

    datasource_entry_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
        datasource.type,
    )
    datasource_entry_handler: DataPipeline = datasource_entry_handler_cls(
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
