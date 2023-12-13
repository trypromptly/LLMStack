import logging 

from typing import List, Optional
from pydantic import Field
from llmstack.common.utils.splitter import SpacyTextSplitter
from llmstack.common.utils.text_extract import ExtraParams, extract_text_elements
from llmstack.datasources.handlers.datasource_processor import DataSourceSchema
from llmstack.datasources.handlers.datasource_processor import DataSourceEntryItem, DataSourceSyncConfiguration, DataSourceSyncType, DataSourceSchema, DataSourceProcessor, WEAVIATE_SCHEMA
from llmstack.datasources.models import DataSource

from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.common.utils.crawlers import run_url_spider_in_process

logger = logging.getLogger(__file__)

class LoggedInURLSchema(DataSourceSchema):
    urls: str = Field(description='URLs to scrape, List of URL can be comma separated.', widget='textarea', max_length=1600)
    connection_id: Optional[str] = Field(description='Select connection if parsing loggedin page', widget='connection')
    
    @staticmethod
    def get_content_key() -> str:
        return 'page_content'

    @staticmethod
    def get_weaviate_schema(class_name: str) -> dict:
        return WEAVIATE_SCHEMA.safe_substitute(
            class_name=class_name,
            content_key=LoggedInURLSchema.get_content_key(),
        )
        
class LoggedInURLDataSource(DataSourceProcessor[LoggedInURLSchema]):
    def __init__(self, datasource: DataSource):
        super().__init__(datasource)

    @staticmethod
    def name() -> str:
        return 'loggedin_url'

    @staticmethod
    def slug() -> str:
        return 'loggedin_url'

    @staticmethod
    def description() -> str:
        return 'Used to scrape loggedin/internal pages'

    @staticmethod
    def provider_slug() -> str:
        return 'promptly'

    @classmethod
    def get_sync_configuration(cls) -> Optional[dict]:
        return DataSourceSyncConfiguration(sync_type=DataSourceSyncType.FULL).dict()

    def get_url_data(self, url: str, connection_id = None) -> Optional[DataSourceEntryItem]:
        if not url.startswith('https://') and not url.startswith('http://'):
            url = f'https://{url}'
        connection = self._env['connections'].get(connection_id, None) if connection_id else None
                
        result = run_url_spider_in_process(url=url, use_renderer=True, connection=connection)
        data = result[0]['html_page'].encode('utf-8')
        elements = extract_text_elements(mime_type='text/html',data=data,
                                         file_name=url.split('/')[-1],
                                         charset='utf-8', 
                                         extra_params=ExtraParams())
        text = '\n\n'.join([str(el) for el in elements])
        logger.info(f'Got result from spider: {text}')

        docs = [
            Document(
                page_content_key=self.get_content_key(), page_content=t, metadata={
                    'source': url,
                },
            ) for t in SpacyTextSplitter(chunk_size=1500, length_func=len).split_text(text)
        ]
        return docs

    def validate_and_process(self, data: dict) -> List[DataSourceEntryItem]:
        loggedin_url_input = LoggedInURLSchema(**data)            
        # Split urls by newline and then by comma
        urls = [
            url.strip().rstrip() for url_list in [
                url.split(',') for url in loggedin_url_input.urls.split('\n')
            ] for url in url_list
        ]
        # Filter out empty urls
        urls = list(set(list(filter(lambda url: url != '', urls))))
        return list(map(lambda x: DataSourceEntryItem(name=x, data={'url': x, 'connection_id' : loggedin_url_input.connection_id}), urls))

    def get_data_documents(self, data: DataSourceEntryItem) -> Optional[DataSourceEntryItem]: 
        return self.get_url_data(data.data['url'], connection_id=data.data['connection_id'])
