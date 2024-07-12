import logging
import uuid

from rq import get_current_job

from llmstack.data.models import DataSource, DataSourceEntry, DataSourceEntryStatus
from llmstack.data.types import DataSourceTypeFactory
from llmstack.jobs.models import AdhocJob, TaskRunLog

logger = logging.getLogger(__name__)


def process_datasource_add_entry_request(
    datasource_id,
    input_data,
    job_id,
    **kwargs,
):
    from llmstack.jobs.jobs import upsert_datasource_entries_task

    job = get_current_job()
    adhoc_job = AdhocJob.objects.get(uuid=uuid.UUID(job_id))

    adhoc_job.job_id = job.id
    adhoc_job.status = "started"
    adhoc_job.save()

    datasource = DataSource.objects.get(uuid=uuid.UUID(datasource_id))
    datasource_entry_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
        datasource.type,
    )
    datasource_entry_handler = datasource_entry_handler_cls(datasource)

    datasource_entry_items = datasource_entry_handler.validate_and_process(
        input_data,
    )
    datasource_entry_items = list(
        map(lambda x: x.model_dump(), datasource_entry_items),
    )

    datasource_entries = []
    for item in datasource_entry_items:
        datasourceentry_obj = DataSourceEntry.objects.create(
            datasource=datasource,
            name=item.get("name"),
            status=DataSourceEntryStatus.PROCESSING,
        )
        item["uuid"] = str(datasourceentry_obj.uuid)
        datasource_entries.append(item)

    task_run_log = TaskRunLog(
        task_type=adhoc_job.TASK_TYPE,
        task_id=adhoc_job.id,
        job_id=job.id,
        status="started",
    )
    task_run_log.save()

    kwargs = {
        "_job_metadata": {
            "task_run_log_uuid": str(task_run_log.uuid),
            "task_job_uuid": job_id,
        },
    }

    results = upsert_datasource_entries_task(
        datasource_id,
        datasource_entries,
        **kwargs,
    )

    task_run_log.result = results
    task_run_log.save()

    return task_run_log.uuid


def extract_urls_task(url):
    from urllib.parse import urlparse

    from llmstack.common.utils.utils import (
        extract_urls_from_sitemap,
        get_url_content_type,
        is_sitemap_url,
        is_youtube_video_url,
        scrape_url,
    )

    url_content_type = get_url_content_type(url=url)
    url_content_type_parts = url_content_type.split(";")
    mime_type = url_content_type_parts[0]

    if is_youtube_video_url(url):
        return [url]

    if mime_type != "text/html" and not is_sitemap_url(url):
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
            hrefs = (
                scrapped_url[0].get("hrefs", [url])
                if len(
                    scrapped_url,
                )
                > 0
                else [url]
            )

            hrefs = list(set(map(lambda x: x.split("?")[0], hrefs)))
            paths = list(filter(lambda x: x.startswith("/"), hrefs))
            fq_urls = list(
                filter(lambda x: not x.startswith("/"), hrefs),
            )

            urls = (
                [
                    url,
                ]
                + list(map(lambda entry: f"{protocol}://{domain}{entry}", paths))
                + fq_urls
            )

            # Make sure everything is a url
            urls = list(
                filter(
                    lambda x: x.startswith(
                        "https://",
                    )
                    or x.startswith("http://"),
                    urls,
                ),
            )

            # Filter out urls that are not from the same domain
            urls = list(
                set(filter(lambda x: urlparse(x).netloc == domain, urls)),
            )

        except Exception as e:
            logger.exception(f"Error while extracting urls: {e}")

        return urls
