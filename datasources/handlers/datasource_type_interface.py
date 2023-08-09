import copy
import json
import logging
from abc import ABC
from string import Template
from typing import Generic
from typing import List
from typing import Optional
from typing import TypeVar

from django.conf import settings
from pydantic import BaseModel

from common.promptly.blocks.embeddings.openai_embedding import EmbeddingAPIProvider
from common.promptly.blocks.embeddings.openai_embedding import OpenAIEmbeddingConfiguration
from common.promptly.blocks.embeddings.openai_embedding import OpenAIEmbeddingInput
from common.promptly.blocks.embeddings.openai_embedding import OpenAIEmbeddingOutput
from common.promptly.blocks.embeddings.openai_embedding import OpenAIEmbeddingsProcessor
from common.promptly.vectorstore import Document
from common.promptly.vectorstore import DocumentQuery
from common.promptly.vectorstore import VectorStoreInterface
from common.promptly.vectorstore.weaviate import Weaviate as PromptlyWeaviate
from datasources.models import DataSource
from base.models import Profile
from base.models import VectorstoreEmbeddingEndpoint

logger = logging.getLogger(__name__)

EntryConfigurationSchemaType = TypeVar('EntryConfigurationSchemaType')

WEAVIATE_SCHEMA = Template('''
    {"classes": [{"class": "$class_name", "description": "Text data source", "vectorizer": "text2vec-openai", "moduleConfig": {"text2vec-openai": {"model": "ada", "type": "text"}}, "properties": [{"name": "$content_key", "dataType": ["text"], "description": "Text",
        "moduleConfig": {"text2vec-openai": {"skip": false, "vectorizePropertyName": false}}}, {"name": "source", "dataType": ["string"], "description": "Document source"}, {"name": "metadata", "dataType": ["string[]"], "description": "Document metadata"}]}]}
''')


class DataSourceSchema(BaseModel):

    """
    This is Base Schema model for all data source type schemas
    """
    @ staticmethod
    def get_vector_fields() -> list:
        raise NotImplementedError

    @ staticmethod
    def get_content_key() -> str:
        raise NotImplementedError

    @ classmethod
    def get_json_schema(cls):
        return super().schema_json(indent=2)

    @ classmethod
    def get_schema(cls):
        return super().schema()

    @ classmethod
    def get_ui_schema(cls):
        schema = cls.get_schema()
        ui_schema = {}
        for key in schema.keys():
            if key == 'properties':
                ui_schema['ui:order'] = list(schema[key].keys())
                ui_schema[key] = {}
                for prop_key in schema[key].keys():
                    ui_schema[key][prop_key] = {}
                    if 'title' in schema[key][prop_key]:
                        ui_schema[key][prop_key]['ui:label'] = schema[key][prop_key]['title']
                    if 'description' in schema[key][prop_key]:
                        ui_schema[key][prop_key]['ui:description'] = schema[key][prop_key]['description']
                    if 'type' in schema[key][prop_key]:
                        if schema[key][prop_key]['type'] == 'string' and prop_key in ('data', 'text', 'content'):
                            ui_schema[key][prop_key]['ui:widget'] = 'textarea'
                        elif schema[key][prop_key]['type'] == 'string':
                            ui_schema[key][prop_key]['ui:widget'] = 'text'
                        elif schema[key][prop_key]['type'] == 'integer' or schema[key][prop_key]['type'] == 'number':
                            ui_schema[key][prop_key]['ui:widget'] = 'updown'
                        elif schema[key][prop_key]['type'] == 'boolean':
                            ui_schema[key][prop_key]['ui:widget'] = 'checkbox'
                    if 'enum' in schema[key][prop_key]:
                        ui_schema[key][prop_key]['ui:widget'] = 'select'
                        ui_schema[key][prop_key]['ui:options'] = {
                            'enumOptions': [
                                {'value': val, 'label': val} for val in schema[key][prop_key]['enum']
                            ],
                        }
                    if 'widget' in schema[key][prop_key]:
                        ui_schema[key][prop_key]['ui:widget'] = schema[key][prop_key]['widget']
                    if 'format' in schema[key][prop_key] and schema[key][prop_key]['format'] == 'date-time':
                        ui_schema[key][prop_key]['ui:widget'] = 'datetime'
            else:
                ui_schema[key] = copy.deepcopy(schema[key])
        return ui_schema['properties']


class DataSourceEntryItem(BaseModel):
    """
    This is the response model for a single data source entry
    """
    uuid: str = ''
    name: str = ''
    config: dict = {}
    size: int = 0
    metadata: dict = {}
    data: Optional[dict] = None


class DataSourceTypeInterface(Generic[EntryConfigurationSchemaType], ABC):
    @staticmethod
    def name(self) -> str:
        raise NotImplementedError

    @staticmethod
    def slug() -> str:
        raise NotImplementedError

    @classmethod
    def get_entry_config_schema(cls) -> EntryConfigurationSchemaType:
        datasource_type_interface = cls.__orig_bases__[0]
        return datasource_type_interface.__args__[0].get_schema()

    @classmethod
    def get_entry_config_ui_schema(cls) -> EntryConfigurationSchemaType:
        datasource_type_interface = cls.__orig_bases__[0]
        return datasource_type_interface.__args__[0].get_ui_schema()

    @classmethod
    def get_content_key(cls) -> str:
        datasource_type_interface = cls.__orig_bases__[0]
        return datasource_type_interface.__args__[0].get_content_key()

    @classmethod
    def get_weaviate_schema(cls, class_name: str) -> dict:
        datasource_type_interface = cls.__orig_bases__[0]
        return datasource_type_interface.__args__[0].get_weaviate_schema(class_name)

    @property
    def datasource_class_name(self):
        return 'Datasource_' + str(self.datasource.uuid).replace('-', '_')

    @property
    def vectorstore(self) -> VectorStoreInterface:
        return self._vectorstore

    @property
    def embeddings_endpoint(self):
        return self._embeddings_endpoint

    def __init__(self, datasource: DataSource):
        self.datasource = datasource
        self.profile = Profile.objects.get(user=self.datasource.owner)

        vectorstore_embedding_endpoint = self.profile.vectostore_embedding_endpoint
        vectorstore_embeddings_batch_size = self.profile.vectorstore_embeddings_batch_size
        vectorstore_embedding_rate_limit = self.profile.weaviate_embeddings_api_rate_limit

        promptly_weaviate = None
        embedding_endpoint_configuration = None

        if vectorstore_embedding_endpoint == VectorstoreEmbeddingEndpoint.OPEN_AI:
            promptly_weaviate = PromptlyWeaviate(
                url=self.profile.weaviate_url,
                openai_key=self.profile.get_vendor_key('openai_key'),
                weaviate_rw_api_key=self.profile.weaviate_api_key,
                embeddings_rate_limit=vectorstore_embedding_rate_limit,
                embeddings_batch_size=vectorstore_embeddings_batch_size,
            )
            embedding_endpoint_configuration = OpenAIEmbeddingConfiguration(
                api_type=EmbeddingAPIProvider.OPENAI,
                model='text-embedding-ada-002',
                api_key=self.profile.get_vendor_key('openai_key'),
            )
        else:

            promptly_weaviate = PromptlyWeaviate(
                url=self.profile.weaviate_url,
                azure_openai_key=self.profile.get_vendor_key(
                    'azure_openai_api_key',
                ),
                weaviate_rw_api_key=self.profile.weaviate_api_key,
                embeddings_rate_limit=vectorstore_embedding_rate_limit,
                embeddings_batch_size=vectorstore_embeddings_batch_size,
            )
            embedding_endpoint_configuration = OpenAIEmbeddingConfiguration(
                api_type=EmbeddingAPIProvider.AZURE_OPENAI,
                endpoint=self.profile.weaviate_text2vec_config['resourceName'],
                deploymentId=self.profile.weaviate_text2vec_config['deploymentId'],
                apiVersion='2022-12-01',
                api_key=self.profile.get_vendor_key('azure_openai_api_key'),
            )

        # Get Weaviate schema
        weaviate_schema = json.loads(
            self.get_weaviate_schema(self.datasource_class_name),
        )
        weaviate_schema['classes'][0]['moduleConfig']['text2vec-openai'] = self.profile.weaviate_text2vec_config
        # Create an index for the datasource
        promptly_weaviate.get_or_create_index(
            index_name=self.datasource_class_name,
            schema=json.dumps(weaviate_schema),
        )

        self._vectorstore = promptly_weaviate

        if self.profile.use_custom_embedding:
            self._embeddings_endpoint = OpenAIEmbeddingsProcessor(
                configuration=embedding_endpoint_configuration.dict(),
            )
        else:
            self._embeddings_endpoint = None

    def validate_and_process(self, data: dict) -> List[DataSourceEntryItem]:
        raise NotImplementedError

    def get_data_documents(self, data: dict) -> List[Document]:
        raise NotImplementedError

    def _get_document_embeddings(self, text: str) -> OpenAIEmbeddingOutput:
        if self.embeddings_endpoint:
            logger.info(f'Generating embeddings')
            return self.embeddings_endpoint.process(OpenAIEmbeddingInput(text=text).dict()).embeddings
        else:
            return None

    def add_entry(self, data: dict) -> Optional[DataSourceEntryItem]:
        documents = self.get_data_documents(data)

        documents = map(
            lambda document: Document(
                page_content_key=document.page_content_key,
                page_content=document.page_content, metadata={
                    **document.metadata, **data.metadata,
                },
                embeddings=self._get_document_embeddings(
                    document.page_content),
            ), documents,
        )

        document_ids = self.vectorstore.add_texts(
            index_name=self.datasource_class_name, documents=documents,
        )
        logger.info(f'Added {len(document_ids)} documents to vectorstore.')
        return data.copy(update={'config': {'document_ids': document_ids}, 'size': 1536 * 4 * len(document_ids)})

    def similarity_search(self, query: str, **kwargs) -> List[dict]:

        document_query = DocumentQuery(
            query=query, page_content_key=self.get_content_key(
            ), limit=kwargs.get('limit', 2), metadata={'additional_properties': ['source']}, search_filters=kwargs.get('search_filters', None),
        )

        return self.vectorstore.similarity_search(
            index_name=self.datasource_class_name, document_query=document_query, **kwargs,
        )

    def hybrid_search(self, query: str, **kwargs) -> List[dict]:
        document_query = DocumentQuery(
            query=query, page_content_key=self.get_content_key(
            ), limit=kwargs.get('limit', 2), metadata={'additional_properties': ['source']}, search_filters=kwargs.get('search_filters', None), alpha=kwargs.get('alpha', 0.75),
        )
        return self.vectorstore.hybrid_search(
            index_name=self.datasource_class_name, document_query=document_query, **kwargs,
        )

    def delete_entry(self, data: dict) -> None:
        if 'document_ids' in data and isinstance(data['document_ids'], list):
            for document_id in data['document_ids']:
                logger.info(
                    f'Deleting document {document_id} from vectorstore.',
                )
                self.vectorstore._client.data_object.delete(
                    document_id, self.datasource_class_name,
                )

    def delete_all_entries(self) -> None:
        self.vectorstore._client.schema.delete_class(
            self.datasource_class_name,
        )

    def get_entry_text(self, data: dict) -> str:
        result = []
        document = {}
        if 'document_ids' in data and isinstance(data['document_ids'], list):
            for document_id in data['document_ids'][:20]:
                content_key = self.get_content_key()
                document = self.vectorstore._client.data_object.get(
                    document_id,
                ).get('properties')
                result.append(document.get(content_key, ''))
        metadata = dict(
            map(
                lambda x: (x, document.get(x, '')), [
                    y for y in document.keys() if y != content_key
                ],
            ),
        )
        return metadata, '\n'.join(result)
