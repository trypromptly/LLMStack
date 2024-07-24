import logging
import urllib.parse
import uuid
from typing import List, Optional

from asgiref.sync import async_to_sync
from django.shortcuts import get_object_or_404
from pydantic import BaseModel, Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.data.models import DataSource
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class DataSourceSearchInput(ApiProcessorSchema):
    query: str


class DocumentMetadata(BaseModel):
    certainty: float = Field(0.0, description="Certainty of the document")
    distance: float = Field(0.0, description="Distance of the document")
    score: Optional[float] = Field(None, description="Score of the document")


class Document(ApiProcessorSchema):
    content: str = Field(
        None,
        description="Content of the document",
        json_schema_extra={"widget": "textarea"},
    )
    source: Optional[str] = Field(description="Source of the document")
    metadata: DocumentMetadata = Field(description="Metadata of the document")
    additional_properties: Optional[dict] = {}


class DataSourceSearchOutput(ApiProcessorSchema):
    answers: List[Document] = []
    answers_text: str = Field(description="All answers as text")


class DataSourceSearchConfigurations(ApiProcessorSchema):
    datasources: List[str] = Field(
        None,
        description="Datasource to use",
        json_schema_extra={"advanced_parameter": False, "widget": "datasource"},
    )
    document_limit: int = Field(
        default=4,
        description="Limit of documents to return",
    )
    search_filters: Optional[str] = Field(
        title="Search filters",
        default=None,
        description="Search filters on datasource entry metadata. You can provide search filters like `source == url1 || source == url2`. Click on your data entries to get your metadata",
    )
    hybrid_semantic_search_ratio: Optional[float] = Field(
        default=0.75,
        description="Ratio of semantic search to hybrid search",
        ge=0.0,
        le=1.0,
        multiple_of=0.01,
    )


class DataSourceSearchProcessor(
    ApiProcessorInterface[DataSourceSearchInput, DataSourceSearchOutput, DataSourceSearchConfigurations],
):
    @staticmethod
    def name() -> str:
        return "Datasource Search"

    @staticmethod
    def slug() -> str:
        return "datasource_search"

    @staticmethod
    def description() -> str:
        return "Search across your data sources"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    @classmethod
    def get_output_template(cls) -> Optional[OutputTemplate]:
        return OutputTemplate(markdown="""{{ answers_text }}""")

    def process(self) -> DataSourceSearchOutput:
        input_data = self._input
        hybrid_semantic_search_ratio = self._config.hybrid_semantic_search_ratio

        documents = []
        for datasource_uuid in self._config.datasources:
            datasource = get_object_or_404(DataSource, uuid=uuid.UUID(datasource_uuid))
            pipeline = datasource.create_data_query_pipeline()
            try:
                result = pipeline.search(
                    query=input_data.query,
                    alpha=hybrid_semantic_search_ratio,
                    limit=self._config.document_limit,
                    search_filters=self._config.search_filters,
                    use_hybrid_search=True,
                )
                documents.extend(result)
            except BaseException:
                logger.exception("Error while searching")
                raise Exception("Error while searching")

        if documents and len(documents) > 0:
            if "score" in documents[0].metadata:
                documents = sorted(
                    documents,
                    key=lambda d: d.metadata["score"],
                    reverse=True,
                )[: self._config.document_limit]
            else:
                documents = documents[: self._config.document_limit]

        answers = []
        answer_text = ""
        for document in documents:
            source = document.metadata.get(
                "source",
                None,
            )
            if source:
                source = urllib.parse.unquote(source)
            answers.append(
                Document(
                    content=document.page_content,
                    source=source,
                    metadata=DocumentMetadata(
                        certainty=document.metadata["certainty"] if "certainty" in document.metadata else 0.0,
                        distance=document.metadata["distance"] if "distance" in document.metadata else 0.0,
                        score=document.metadata["score"] if "score" in document.metadata else None,
                    ),
                    additional_properties=document.metadata,
                ),
            )
            answer_text += f"Content: {document.page_content} \n\nSource: {source} \n\n\n\n"

        async_to_sync(self._output_stream.write)(
            DataSourceSearchOutput(
                answers=answers,
                answers_text=answer_text,
            ),
        )
        output = self._output_stream.finalize()

        return output
