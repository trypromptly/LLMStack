import json
import logging

from typing import Dict, List
from typing import Optional

from pydantic import Field
import weaviate

from common.blocks.base.schema import BaseSchema as _Schema
from common.blocks.data.store.vectorstore import Document
from common.blocks.data.store.vectorstore.weaviate import generate_where_filter
from common.utils.models import Config
from datasources.handlers.datasource_type_interface import DataSourceEntryItem
from datasources.handlers.datasource_type_interface import DataSourceSchema
from datasources.handlers.datasource_type_interface import DataSourceProcessor
from datasources.models import DataSource


logger = logging.getLogger(__name__)

class WeaviateConnection(_Schema):
    weaviate_url: str = Field(description='Weaviate URL')
    username: Optional[str] = Field(description='Weaviate username')
    password: Optional[str] = Field(description='Weaviate password')
    api_key: Optional[str] = Field(description='Weaviate API key')
    additional_headers: Optional[str] = Field(description='Weaviate headers. Please enter a JSON string.', widget='textarea', default='{}')
    
class WeaviateDatabaseSchema(DataSourceSchema):
    index_name: str = Field(description='Weaviate index name')
    content_property_name: str = Field(description='Weaviate content property name')
    additional_properties: Optional[List[str]] = Field(description='Weaviate additional properties', default=['certainty', 'distance'])
    connection: Optional[WeaviateConnection] = Field(description='Weaviate connection string')


class WeaviateConnectionConfiguration(Config):
    config_type = 'weaviate_connection'
    is_encrypted = True
    weaviate_config: Optional[Dict]
    
class WeaviateDataSource(DataSourceProcessor[WeaviateDatabaseSchema]):
    def __init__(self, datasource: DataSource):
        self.datasource = datasource
        if self.datasource.config and 'data' in self.datasource.config:
            config_dict = WeaviateConnectionConfiguration().from_dict(self.datasource.config, self.datasource.profile.decrypt_value)
            self._configuration = WeaviateDatabaseSchema(**config_dict['weaviate_config'])
        
    @staticmethod
    def name() -> str:
        return 'Weaviate'
    
    @staticmethod 
    def slug() -> str:
        return 'weaviate'
    
    @staticmethod
    def process_validate_config(config_data: dict, datasource: DataSource) -> dict:
        return WeaviateConnectionConfiguration(weaviate_config=config_data).to_dict(encrypt_fn=datasource.profile.encrypt_value)
    
    @staticmethod
    def provider_slug() -> str:
        return 'weaviate'
    
    def validate_and_process(self, data: dict) -> List[DataSourceEntryItem]:
        raise NotImplementedError

    def get_data_documents(self, data: dict) -> List[Document]:
        raise NotImplementedError
    
    def add_entry(self, data: dict) -> Optional[DataSourceEntryItem]:
        raise NotImplementedError
    
    def _get_client(self):
        if self._configuration.connection.username and self._configuration.connection.password:
            return weaviate.Client(
                url=self._configuration.connection.weaviate_url,
                auth_client_secret=weaviate.AuthClientPassword(username=self._configuration.connection.username, password=self._configuration.connection.password), 
                additional_headers=json.loads(self._configuration.connection.additional_headers) if self._configuration.connection.additional_headers else {},
            )
        elif self._configuration.connection.api_key:
            return weaviate.Client(
                url=self._configuration.connection.weaviate_url,
                auth_client_secret=weaviate.AuthApiKey(api_key=self._configuration.connection.api_key),
                additional_headers=json.loads(self._configuration.connection.additional_headers) if self._configuration.connection.additional_headers else {},
            )
        else:
            return weaviate.Client(
                url=self._configuration.connection.weaviate_url,
                additional_headers=json.loads(self._configuration.connection.additional_headers) if self._configuration.connection.additional_headers else {},
            )
        
    def similarity_search(self, query: str, **kwargs) -> List[dict]:
        result = []
        
        properties = [self._configuration.content_property_name]
        additional_properties = ['id'] + self._configuration.additional_properties
        index_name = self._configuration.index_name
        nearText = {'concepts': query}

        # Add filters
        whereFilter = {}
        if kwargs.get('search_filters', None):
            # Build weaviate where filter from search_filters string
            # Example: "source == website_crawler || source == test"
            try:
                whereFilter = generate_where_filter(
                    kwargs.get('search_filters', None),
                )
            except Exception as e:
                logger.error('Error in generating where filter: %s' % e)
                
        document_limit = kwargs.get('document_limit', 2)

        client = self._get_client()
        
        try:
            query_obj = client.query.get(index_name, properties)
            
            if whereFilter:
                query_obj = query_obj.with_where(whereFilter)
                
            if kwargs.get('search_distance'):
                nearText['certainty'] = kwargs.get('search_distance')

            query_response = query_obj.with_near_text(nearText).with_limit(document_limit,).with_additional(additional_properties).do()
            
        except Exception as e:
            logger.error('Error in similarity search: %s' % e)
            raise e

        if 'data' not in query_response or 'Get' not in query_response['data'] or index_name not in query_response['data']['Get']:
            logger.error(
                'Invalid response from Weaviate: %s Index Name: %s' %
                query_response, index_name,
            )
            raise Exception('Error in fetching data from document store')
        
        if 'errors' in query_response and len(query_response['errors']) > 0:
            raise Exception('Error in fetching data from document store')

        if query_response['data']['Get'][index_name] is None:
            return result

        for res in query_response['data']['Get'][index_name]:
            additional_properties = {}

            text = res.pop(self._configuration.content_property_name, None)
            _document_search_properties = res.pop('_additional')
            for document_property in additional_properties:
                if document_property in res:
                    additional_properties[document_property] = res.pop(
                        document_property,
                    )

            result.append(
                Document(
                    page_content_key=self._configuration.content_property_name, page_content=text, metadata={
                        **additional_properties, **_document_search_properties},
                ),
            )

        return result
            
    def hybrid_search(self, query: str, **kwargs) -> List[dict]:
        raise NotImplementedError
    
    def delete_entry(self, data: dict) -> None:
        raise NotImplementedError
    
    def resync_entry(self, data: dict) -> Optional[DataSourceEntryItem]:
        raise NotImplementedError 
    
    def delete_all_entries(self) -> None:
        raise NotImplementedError 
    
    def get_entry_text(self, data: dict) -> str:
        return None, self._configuration.json()