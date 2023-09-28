import logging
import urllib.parse
import uuid
from typing import List
from typing import Optional

from asgiref.sync import async_to_sync
from django.shortcuts import get_object_or_404
from pydantic import BaseModel
from pydantic import Field

from llmstack.datasources.models import DataSource
from llmstack.datasources.types import DataSourceTypeFactory
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface, ApiProcessorSchema

logger = logging.getLogger(__name__)


class DataSourceSearchInput(ApiProcessorSchema):
    query: str


class DocumentMetadata(BaseModel):
    certainty: float = Field(0.0, description='Certainty of the document')
    distance: float = Field(0.0, description='Distance of the document')


class Document(ApiProcessorSchema):
    content: str = Field(
        None, description='Content of the document', widget='text',
    )
    source: Optional[str] = Field(description='Source of the document')
    metadata: DocumentMetadata = Field(description='Metadata of the document')
    additional_properties: Optional[dict] = {}


class DataSourceSearchOutput(ApiProcessorSchema):
    answers: List[Document] = []
    answers_text: str = Field(description='All answers as text')


class DataSourceSearchConfigurations(ApiProcessorSchema):
    datasources: List[str] = Field(
        None,
        description='Datasource to use', widget='datasource', advanced_parameter=False,
    )
    document_limit: int = Field(
        default=4, description='Limit of documents to return',
    )
    search_filters: str = Field(
        title='Search filters', default=None, description='Search filters on datasource entry metadata. You can provide search filters like `source == url1 || source == url2`. Click on your data entries to get your metadata', advanced_parameter=True,
    )
    hybrid_semantic_search_ratio: Optional[float] = Field(
        default=0.75, description='Ratio of semantic search to hybrid search', ge=0.0, le=1.0, multiple_of=0.01
    )


class DataSourceSearchProcessor(ApiProcessorInterface[DataSourceSearchInput, DataSourceSearchOutput, DataSourceSearchConfigurations]):
    @staticmethod
    def name() -> str:
        return 'Datasource Search'

    @staticmethod
    def slug() -> str:
        return 'datasource_search'

    @staticmethod
    def description() -> str:
        return 'Search across your data sources'

    @staticmethod
    def provider_slug() -> str:
        return 'promptly'

    def process(self) -> DataSourceSearchOutput:
        input_data = self._input
        hybrid_semantic_search_ratio = self._config.hybrid_semantic_search_ratio

        documents = []
        for datasource_uuid in self._config.datasources:
            datasource = get_object_or_404(
                DataSource, uuid=uuid.UUID(datasource_uuid),
            )

            datasource_entry_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
                datasource.type,
            )
            datasource_entry_handler = datasource_entry_handler_cls(datasource)

            try:
                documents.extend(
                    datasource_entry_handler.search(
                        query=input_data.query,
                        alpha=hybrid_semantic_search_ratio,
                        limit=self._config.document_limit,
                        search_filters=self._config.search_filters,
                        use_hybrid_search=True,
                    ),
                )
            except:
                logger.exception('Error while searching')
                raise Exception('Error while searching')

        answers = []
        answer_text = ''
        for document in documents:
            source = document.metadata.get(
                'source', None,
            )
            if source:
                source = urllib.parse.unquote(source)
            answers.append(
                Document(
                    content=document.page_content,
                    source=source,
                    metadata=DocumentMetadata(
                        certainty=document.metadata['certainty'] if 'certainty' in document.metadata else 0.0,
                        distance=document.metadata['distance'] if 'distance' in document.metadata else 0.0,
                    ),
                    additional_properties=document.metadata
                ),
            )
            answer_text += f'Content: {document.page_content} \n\nSource: {source} \n\n\n\n'

        async_to_sync(self._output_stream.write)(
            DataSourceSearchOutput(
                answers=answers, answers_text=answer_text,
            ),
        )
        output = self._output_stream.finalize()

        return output
