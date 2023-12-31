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


def extract_urls_task(url):
    from urllib.parse import urlparse
    from llmstack.common.utils.utils import extract_urls_from_sitemap
    from llmstack.common.utils.utils import get_url_content_type
    from llmstack.common.utils.utils import is_sitemap_url
    from llmstack.common.utils.utils import is_youtube_video_url
    from llmstack.common.utils.utils import scrape_url

    url_content_type = get_url_content_type(url=url)
    url_content_type_parts = url_content_type.split(';')
    mime_type = url_content_type_parts[0]

    if is_youtube_video_url(url):
        return [url]

    if mime_type != 'text/html' and not is_sitemap_url(url):
        return [url]

    # Get url domain
    domain = urlparse(url).netloc
    protocol = urlparse(url).scheme

    if is_sitemap_url(url):
        urls = extract_urls_from_sitemap(url)
        return urls
    else:
        urls = [url]
        try:
            scrapped_url = scrape_url(url)
            hrefs = scrapped_url[0].get('hrefs', [url]) if len(
                scrapped_url,
            ) > 0 else [url]

            hrefs = list(set(map(lambda x: x.split('?')[0], hrefs)))
            paths = list(filter(lambda x: x.startswith('/'), hrefs))
            fq_urls = list(
                filter(lambda x: not x.startswith('/'), hrefs),
            )

            urls = [
                url,
            ] + list(map(lambda entry: f'{protocol}://{domain}{entry}', paths)) + fq_urls

            # Make sure everything is a url
            urls = list(
                filter(
                    lambda x: x.startswith(
                        'https://',
                    ) or x.startswith('http://'), urls,
                ),
            )

            # Filter out urls that are not from the same domain
            urls = list(
                set(filter(lambda x: urlparse(x).netloc == domain, urls)),
            )

        except Exception as e:
            logger.exception(f'Error while extracting urls: {e}')

        return urls
