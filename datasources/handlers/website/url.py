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


class URLSchema(DataSourceSchema):
    urls: str = Field(
        widget='webpageurls', description='URLs to scrape, List of URL can be comma or newline separated. If site.xml is present, it will be used to scrape the site.', max_length=1600,
    )

    @staticmethod
    def get_content_key() -> str:
        return 'page_content'

    @staticmethod
    def get_weaviate_schema(class_name: str) -> dict:
        return WEAVIATE_SCHEMA.safe_substitute(
            class_name=class_name,
            content_key=URLSchema.get_content_key(),
        )


class URLDataSource(DataSourceProcessor[URLSchema]):
    def __init__(self, datasource: DataSource):
        super().__init__(datasource)
        profile = Profile.objects.get(user=self.datasource.owner)
        self.openai_key = profile.get_vendor_key('openai_key')

    @staticmethod
    def name() -> str:
        return 'url'

    @staticmethod
    def slug() -> str:
        return 'url'

    def validate_and_process(self, data: dict) -> List[DataSourceEntryItem]:
        entry = URLSchema(**data)
        sitemap_urls = []
        # Split urls by newline and then by comma
        urls = entry.urls.split('\n')
        urls = [
            url.strip().rstrip() for url_list in [
                url.split(',') for url in urls
            ] for url in url_list
        ]
        # Filter out empty urls
        urls = list(set(list(filter(lambda url: url != '', urls))))
        sitemap_xmls = list(
            filter(lambda url: url.endswith('.xml'), urls),
        )
        # Filter out sitemap.xml
        urls = list(filter(lambda url: not url.endswith('.xml'), urls))
        # If sitemap.xml is present, scrape the site to extract urls
        try:
            for sitemap_xml in sitemap_xmls:
                sitmap_xml_urls = extract_urls_from_sitemap(sitemap_xml)
                for sitmap_xml_url in sitmap_xml_urls:
                    sitemap_urls.append(sitmap_xml_url)
        except:
            logger.exception('Error in extracting urls from sitemap')

        return list(map(lambda entry: DataSourceEntryItem(name=entry, data={'url': entry}), urls + sitemap_urls))

    def get_data_documents(self, data: DataSourceEntryItem) -> Optional[DataSourceEntryItem]:
        url = data.data['url']
        if not url.startswith('https://') and not url.startswith('http://'):
            url = f'https://{url}'

        text = extract_text_from_url(
            url, extra_params=ExtraParams(openai_key=self.openai_key),
        )
        docs = [
            Document(
                page_content_key=self.get_content_key(), page_content=t, metadata={
                    'source': url,
                },
            ) for t in SpacyTextSplitter(chunk_size=1500, length_func=len).split_text(text)
        ]
        return docs

    def similarity_search(self, query: str, *args, **kwargs) -> List[dict]:
        return super().similarity_search(query, *args, **kwargs)
