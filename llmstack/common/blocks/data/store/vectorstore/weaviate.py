import json
import logging
import re
import time
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from uuid import uuid4

import weaviate
from pydantic import BaseModel
from weaviate.util import get_valid_uuid

from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.common.blocks.data.store.vectorstore import DocumentQuery
from llmstack.common.blocks.data.store.vectorstore import VectorStoreInterface

logger = logging.getLogger(__name__)


def generate_where_filter(input_string):
    if '&&' in input_string:
        and_operands = input_string.split('&&')
        return {
            'operator': 'And',
            'operands': handle_operands(and_operands),
        }
    elif '||' in input_string:
        or_operands = input_string.split('||')
        return {
            'operator': 'Or',
            'operands': handle_operands(or_operands),
        }
    else:
        return convert_to_json(input_string)


def handle_operands(operands):
    result = []
    for operand in operands:
        result.append(generate_where_filter(operand.strip()))
    return result


def convert_to_json(input_string):
    operator_mapping = {
        '==': 'Equal',
        '>': 'GreaterThan',
        '<': 'LessThan',
        'LIKE': 'Like',
    }

    path, operator, value = re.split(r'\s*(==|>|<|LIKE)\s*', input_string)

    if operator == 'LIKE':
        value = '*' + value.strip('"') + '*'
        value_type = 'valueText' if path.startswith('md_') else 'valueString'
    elif value.isdigit():
        value = int(value)
        value_type = 'valueInt'
    else:
        value = value.strip('"')
        value_type = 'valueText' if path.startswith('md_') else 'valueString'

    return {
        'path': [path],
        'operator': operator_mapping[operator],
        value_type: value,
    }


class WeaviateConfiguration(BaseModel):
    _type = 'weaviate'
    url: str
    openai_key: Optional[str]
    cohere_api_key: Optional[str]
    huggingface_api_key: Optional[str]
    azure_openai_key: Optional[str]
    weaviate_rw_api_key: Optional[str] = None
    embeddings_rate_limit: Optional[int] = 3000
    default_batch_size: Optional[int] = 20
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    additional_headers: Optional[dict] = {}


class Weaviate(VectorStoreInterface):
    """
    Weaviate VectorStore implementation.
    """

    """
    Weaviate VectorStore implementation. Weaviate can use OpenAI, Cohere and HuggingFace API keys
    """

    def __init__(self, *args, **kwargs) -> None:
        configuration = WeaviateConfiguration(**kwargs)

        DEFAULT_BATCH_SIZE = configuration.default_batch_size
        # Rely on the retry mechanism to push through, revisit if this is not enough
        NUM_OBJECTS_PER_SECOND = (configuration.embeddings_rate_limit / 60)

        def check_batch_result(results: Optional[List[Dict[str, Any]]]) -> None:
            """
            Check batch results for errors.

            Parameters
            ----------
            results : dict
                The Weaviate batch creation return value.
            """
            time_took_to_create_batch = DEFAULT_BATCH_SIZE * (
                self._client.batch.creation_time /
                self._client.batch.batch_size
            )

            time.sleep(
                max(
                    DEFAULT_BATCH_SIZE/NUM_OBJECTS_PER_SECOND -
                    time_took_to_create_batch, 0,
                ),
            )

            if results is None:
                return
            for result in results:
                if 'result' in result and 'errors' in result['result']:

                    if 'error' in result['result']['errors']:
                        logger.error(
                            'Error in document creation: {}'.format(
                                json.dumps(result['result']['errors']),
                            ),
                        )

        headers = configuration.additional_headers
        if configuration.openai_key is not None:
            headers['X-OpenAI-Api-Key'] = configuration.openai_key
        if configuration.cohere_api_key is not None:
            headers['X-Cohere-Api-Key'] = configuration.cohere_api_key
        if configuration.huggingface_api_key is not None:
            headers['X-HuggingFace-Api-Key'] = configuration.huggingface_api_key
        if configuration.azure_openai_key is not None:
            headers['X-Azure-Api-Key'] = configuration.azure_openai_key
        if configuration.weaviate_rw_api_key is not None:
            headers['authorization'] = 'Bearer ' + \
                configuration.weaviate_rw_api_key

        if configuration.username is not None and configuration.password is not None:
            self._client = weaviate.Client(
                url=configuration.url,
                auth_client_secret=weaviate.AuthClientPassword(
                    username=configuration.username, password=configuration.password),
                additional_headers=headers,
            )
        elif configuration.api_key is not None:
            self._client = weaviate.Client(
                url=configuration.url,
                auth_client_secret=weaviate.AuthApiKey(
                    api_key=configuration.api_key),
                additional_headers=headers,
            )
        else:
            self._client = weaviate.Client(
                url=configuration.url,
                additional_headers=headers,
            )

        self.client.batch.configure(
            batch_size=DEFAULT_BATCH_SIZE,
            dynamic=False,
            weaviate_error_retries=weaviate.WeaviateErrorRetryConf(
                number_retries=3, errors_to_include=['429'],
            ),
            callback=check_batch_result,

        )

    def add_text(self, index_name: str, document: Document, **kwargs: Any):
        content_key = document.page_content_key
        content = document.page_content
        metadata = document.metadata
        properties = {content_key: content}
        for metadata_key in metadata.keys():
            properties[metadata_key] = metadata[metadata_key]
        id = get_valid_uuid(uuid4())
        if document.embeddings:
            # Vectors we provided with the document use them
            self.client.data_object.create(
                properties, index_name, id, vector=document.embeddings,
            )
        else:
            self.client.data_object.create(properties, index_name, id)
        return id

    def add_texts(self, index_name: str, documents: List[Document], **kwargs: Any):
        with self.client.batch as batch:
            ids = []
            for document in documents:
                content_key = document.page_content_key
                content = document.page_content
                metadata = document.metadata
                id = get_valid_uuid(uuid4())
                properties = {content_key: content}
                for metadata_key in metadata.keys():
                    properties[metadata_key] = metadata[metadata_key]
                if document.embeddings and len(document.embeddings) > 0:
                    # Vectors we provided with the document use them
                    batch.add_data_object(
                        properties, index_name, id, vector=document.embeddings,
                    )
                else:
                    batch.add_data_object(properties, index_name, id)
                ids.append(id)
        return ids

    def get_or_create_index(self, index_name: str, schema: str, **kwargs: Any):
        try:
            return self.client.schema.get(index_name)
        except weaviate.exceptions.UnexpectedStatusCodeException as e:
            if e.status_code == 404:
                return self.create_index(schema)

    def create_index(self, schema: str, **kwargs: Any):
        self.client.schema.create(json.loads(schema))

    def delete_index(self, index_name: str, **kwargs: Any):
        self.client.schema.delete_class(index_name)

    def delete_document(self, document_id: str, **kwargs: Any):
        self.client.data_object.delete(
            document_id, kwargs['index_name'],
        )

    def get_document_by_id(self, index_name: str, document_id: str, content_key: str):
        try:
            result = self.client.data_object.get(
                uuid=document_id, class_name=index_name)

            return Document(content_key, result['properties'].get(content_key, None), {k: v for k, v in result['properties'].items() if k != content_key})
        except weaviate.exceptions.UnexpectedStatusCodeException as e:
            if e.status_code == 404:
                return None
            else:
                raise e

    def similarity_search(self, index_name: str, document_query: DocumentQuery, **kwargs: Any):
        result = []
        nearText = {'concepts': [document_query.query]}
        whereFilter = {}
        properties = [document_query.page_content_key]
        for key in document_query.metadata.get('additional_properties', []):
            properties.append(key)
        additional_metadata_properties = document_query.metadata.get(
            'metadata_properties', ['id', 'certainty', 'distance'])

        if kwargs.get('search_distance'):
            nearText['certainty'] = kwargs.get('search_distance')

        if document_query.search_filters:
            # Build weaviate where filter from search_filters string
            # Example: "source == website_crawler || source == test"
            try:
                whereFilter = generate_where_filter(
                    document_query.search_filters,
                )
            except Exception as e:
                logger.error('Error in generating where filter: %s' % e)

        try:
            query_obj = self.client.query.get(index_name, properties)
            if whereFilter:
                query_obj = query_obj.with_where(whereFilter)
            query_response = query_obj.with_near_text(nearText).with_limit(
                document_query.limit,
            ).with_additional(additional_metadata_properties).do()
        except Exception as e:
            logger.error('Error in similarity search: %s' % e)
            raise e

        if 'data' not in query_response or 'Get' not in query_response['data'] or index_name not in query_response['data']['Get']:
            logger.error(
                'Invalid response from Weaviate: %s Index Name: %s' %
                query_response, index_name,
            )
            raise Exception('Error in fetching data from document store')

        if query_response['data']['Get'][index_name] is None:
            return result

        for res in query_response['data']['Get'][index_name]:
            additional_properties = {}

            text = res.pop(document_query.page_content_key)
            _document_search_properties = res.pop('_additional')
            for document_property in document_query.metadata.get('additional_properties', []):
                if document_property in res:
                    additional_properties[document_property] = res.pop(
                        document_property,
                    )

            result.append(
                Document(
                    page_content_key=document_query.page_content_key, page_content=text, metadata={
                        **additional_properties, **_document_search_properties},
                ),
            )

        return result

    def hybrid_search(self, index_name: str, document_query: DocumentQuery, **kwargs: Any):
        result = []
        whereFilter = {}
        properties = [document_query.page_content_key]
        for key in document_query.metadata.get('additional_properties', []):
            properties.append(key)

        if document_query.search_filters:
            # Build weaviate where filter from search_filters string
            # Example: "source == website_crawler || source == test"
            try:
                whereFilter = generate_where_filter(
                    document_query.search_filters,
                )
            except Exception as e:
                logger.error('Error in generating where filter: %s' % e)

        try:
            query_obj = self.client.query.get(index_name, properties)
            if whereFilter:
                query_obj = query_obj.with_where(whereFilter)
            query_response = query_obj.with_hybrid(query=document_query.query, alpha=document_query.alpha).with_limit(
                document_query.limit,
            ).with_additional(['id', 'score']).do()
        except Exception as e:
            logger.error('Error in similarity search: %s' % e)
            raise e

        if 'data' not in query_response or 'Get' not in query_response['data'] or index_name not in query_response['data']['Get']:
            logger.error(
                'Invalid response from Weaviate: %s Index Name: %s' %
                query_response, index_name,
            )
            raise Exception('Error in fetching data from document store')

        if query_response['data']['Get'][index_name] is None:
            return result

        for res in query_response['data']['Get'][index_name]:
            additional_properties = {}

            text = res.pop(document_query.page_content_key)
            _document_search_properties = res.pop('_additional')
            for document_property in document_query.metadata.get('additional_properties', []):
                if document_property in res:
                    additional_properties[document_property] = res.pop(
                        document_property,
                    )

            result.append(
                Document(
                    page_content_key=document_query.page_content_key, page_content=text, metadata={
                        **additional_properties, **_document_search_properties},
                ),
            )

        return result
