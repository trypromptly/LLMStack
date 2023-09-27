import logging
from typing import List
from typing import Optional

from pydantic import Field

from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.common.utils.crawlers import run_url_spider_in_process
from llmstack.common.utils.splitter import SpacyTextSplitter
from llmstack.datasources.handlers.datasource_processor import DataSourceEntryItem, DataSourceSchema, DataSourceProcessor, WEAVIATE_SCHEMA

logger = logging.getLogger(__file__)


class WebsiteCrawlerSchema(DataSourceSchema):
    url: str = 'Website URL'
    depth: int = Field(0, description='Depth of the crawler', le=1, ge=0)
    allow_regex: Optional[str] = Field(
        default='.*', description='Regex to allow urls', widget='hidden',
    )
    deny_regex: Optional[str] = Field(
        default='.*', description='Regex to deny urls',  widget='hidden',
    )

    @staticmethod
    def get_content_key() -> str:
        return 'content'

    @staticmethod
    def get_weaviate_schema(class_name: str) -> dict:
        return WEAVIATE_SCHEMA.safe_substitute(
            class_name=class_name,
            content_key=WebsiteCrawlerSchema.get_content_key(),
        )


class WebsiteCrawlerDataSource(DataSourceProcessor[WebsiteCrawlerSchema]):
    @staticmethod
    def name() -> str:
        return 'website crawler'

    @staticmethod
    def slug() -> str:
        return 'website_crawler'

    @staticmethod
    def provider_slug() -> str:
        return 'promptly'

    def validate_and_process(self, data: dict) -> List[DataSourceEntryItem]:
        result = []
        entry = WebsiteCrawlerSchema(**data)
        url_results = run_url_spider_in_process(
            entry.url, entry.depth,
            allowed_domains=None,
            allow_regex=entry.allow_regex,
            deny_regex=entry.deny_regex,
            use_renderer=True,
        )

        for entry in url_results:
            data_source_entry = DataSourceEntryItem(
                name=entry['url'], data=entry, config={},
            )
            result.append(data_source_entry)

        return result

    def get_data_documents(self, data: DataSourceEntryItem) -> DataSourceEntryItem:
        logger.info(
            f'Processing url: {data.name}',
        )
        docs = [
            Document(page_content_key=self.get_content_key(), page_content=t, metadata={'source': data.name}) for t in SpacyTextSplitter(
                chunk_size=1500,
            ).split_text(data.data['html_partition'])
        ]
        return docs
