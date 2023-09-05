import logging
from typing import List
from typing import Optional

from pydantic import Field

from common.blocks.data.store.vectorstore import Document
from common.utils.text_extract import extract_text_from_url
from common.utils.text_extract import ExtraParams
from common.utils.splitter import SpacyTextSplitter
from common.utils.utils import extract_urls_from_sitemap
from datasources.handlers.datasource_type_interface import DataSourceEntryItem
from datasources.handlers.datasource_type_interface import DataSourceSchema
from datasources.handlers.datasource_type_interface import DataSourceProcessor
from datasources.handlers.datasource_type_interface import WEAVIATE_SCHEMA
from datasources.models import DataSource
from base.models import Profile


logger = logging.getLogger(__file__)

"""
Entry configuration schema for url data source type
"""


class SitemapURLSchema(DataSourceSchema):
    url: str = Field(
        description='Sitemap URL to scrape. URL should end with .xml', regex=r'^.*\.xml$',
    )

    @staticmethod
    def get_content_key() -> str:
        return 'page_content'

    @staticmethod
    def get_weaviate_schema(class_name: str) -> dict:
        return WEAVIATE_SCHEMA.safe_substitute(
            class_name=class_name,
            content_key=SitemapURLSchema.get_content_key(),
        )


class SitemapCrawlerDataSource(DataSourceProcessor[SitemapURLSchema]):
    def __init__(self, datasource: DataSource):
        super().__init__(datasource)
        profile = Profile.objects.get(user=self.datasource.owner)
        self.openai_key = profile.get_vendor_key('openai_key')

    @staticmethod
    def name() -> str:
        return 'sitemap_url'

    @staticmethod
    def slug() -> str:
        return 'sitemap_url'

    @staticmethod
    def provider_slug() -> str:
        return 'promptly'

    def validate_and_process(self, data: dict) -> List[DataSourceEntryItem]:
        entry = SitemapURLSchema(**data)
        sitemap_urls = []
        try:
            sitmap_xml_urls = extract_urls_from_sitemap(entry.url)
            for sitmap_xml_url in sitmap_xml_urls:
                sitemap_urls.append(sitmap_xml_url)
        except Exception as e:
            logger.exception('Error in extracting urls from sitemap')

        return list(map(lambda entry: DataSourceEntryItem(name=entry, data={'url': entry}), sitemap_urls))

    def get_data_documents(self, data: DataSourceEntryItem) -> Optional[DataSourceEntryItem]:
        url = data.data['url']
        text = extract_text_from_url(
            url, extra_params=ExtraParams(openai_key=self.openai_key),
        )
        docs = [
            Document(
                page_content_key=self.get_content_key(), page_content=t, metadata={
                    'source': url,
                },
            ) for t in SpacyTextSplitter(chunk_size=1500).split_text(text)
        ]
        return docs

    def similarity_search(self, query: str, *args, **kwargs) -> List[dict]:
        return super().similarity_search(query, *args, **kwargs)
