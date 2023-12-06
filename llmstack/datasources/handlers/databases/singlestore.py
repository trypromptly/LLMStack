from typing import Dict, List, Optional
from pydantic import Field
from llmstack.common.blocks.base.schema import BaseSchema
from llmstack.common.utils.models import Config
from llmstack.datasources.handlers.datasource_processor import DataSourceProcessor, DataSourceSchema
from llmstack.datasources.models import DataSource

class SingleStoreConnection(BaseSchema):
    host: str = Field(description='Host of the SingleStore instance')
    port: int = Field(
        description='Port number to connect to the SingleStore instance')
    database_name: str = Field(description='SingleStore database name')
    username: str = Field(description='SingleStore username')
    password: str = Field(description='SingleStore password')
    database: str = Field(description='SingleStore database name')

class SingleStoreDatabaseSchema(DataSourceSchema):
    connection: Optional[SingleStoreConnection] =  Field(description='SingleStore connection details')
    
class SingleStoreConnectionConfiguration(Config):
    config_type = 'singlestore_connection'
    is_encrypted = True
    singlestore_config: Optional[Dict]
    
class SingleStoreDataSource(DataSourceProcessor[SingleStoreDatabaseSchema]):
    def __init__(self, datasource: DataSource):
        self.datasource = datasource
    
    @staticmethod
    def name() -> str:
        return 'Single Store'
    
    @staticmethod
    def slug() -> str:
        return 'singlestore'
    
    @staticmethod
    def description() -> str:
        return 'Single Store is a distributed SQL database that can be deployed anywhere.'
    
    @staticmethod
    def provider_slug() -> str:
        return 'singlestore'
    
    @staticmethod
    def process_validate_config(config_data: dict, datasource: DataSource) -> dict:
        return  SingleStoreConnectionConfiguration(singlestore_config=config_data).to_dict(
            encrypt_fn=datasource.profile.encrypt_value
        )
        
    def validate_and_process(self, data: dict):
        raise NotImplementedError

    def get_data_documents(self, data: dict):
        raise NotImplementedError

    def add_entry(self, data: dict):
        raise NotImplementedError
    
    def similarity_search(self, query: str, **kwargs) -> List[dict]:
        # TODO: Implement this
        pass 
    
    def hybrid_search(self, query: str, **kwargs) -> List[dict]:
        # TODO: Implement this
        pass 
    
    
    def delete_entry(self, data: dict):
        raise NotImplementedError

    def resync_entry(self, data: dict):
        raise NotImplementedError

    def delete_all_entries(self):
        raise NotImplementedError

    def get_entry_text(self, data: dict) -> str:
        return None, "External Datasource does not support entry text"