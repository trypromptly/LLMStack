import logging
from typing import List

from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.schema import Document as LlamaDocument
from llama_index.core.schema import TextNode

from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.data.models import DataSource
from llmstack.data.schemas import DataDocument

logger = logging.getLogger(__name__)


class DataIngestionPipeline:
    def __init__(self, datasource: DataSource):
        self.datasource = datasource
        self._source_cls = self.datasource.pipeline_obj.source_cls
        self._destination_cls = self.datasource.pipeline_obj.destination_cls

        self._destination = None
        self._transformations = self.datasource.pipeline_obj.transformation_objs
        embedding_cls = self.datasource.pipeline_obj.embedding_cls
        if embedding_cls:
            embedding_additional_kwargs = {
                **self.datasource.pipeline_obj.embedding.data.get("additional_kwargs", {}),
                **{"datasource": datasource},
            }
            self._transformations.append(
                embedding_cls(
                    **{
                        **self.datasource.pipeline_obj.embedding.data,
                        **{"additional_kwargs": embedding_additional_kwargs},
                    }
                )
            )

        if self._destination_cls:
            self._destination = self._destination_cls(**self.datasource.pipeline_obj.destination_data)
            self._destination.initialize_client(datasource=self.datasource)

    def process(self, document: DataDocument) -> DataDocument:
        document = self._source_cls.process_document(document)
        if self.datasource.pipeline_obj.embedding:
            embedding_data = self.datasource.pipeline_obj.embedding.data
            embedding_data["additional_kwargs"] = {
                **embedding_data.get("additional_kwargs", {}),
                **{"datasource": self.datasource},
            }
            embedding_transformer = self.datasource.pipeline_obj.embedding_cls(**embedding_data)
            self._transformations.append(embedding_transformer)

        ingestion_pipeline = IngestionPipeline(transformations=self._transformations)
        ldoc = LlamaDocument(**document.model_dump())
        ldoc.metadata = {**ldoc.metadata, **document.metadata}
        document.nodes = ingestion_pipeline.run(documents=[ldoc])
        document.node_ids = list(map(lambda x: x.id_, document.nodes))
        if self._destination:
            self._destination.add(document=document)

        return document

    def delete_entry(self, document: DataDocument) -> None:
        if self._destination:
            self._destination.delete(document=document)

    def resync_entry(self, data: dict):
        raise NotImplementedError

    def delete_all_entries(self) -> None:
        if self._destination:
            self._destination.delete_collection()


class DataQueryPipeline:
    def __init__(self, datasource: DataSource):
        self.datasource = datasource
        self._destination_cls = self.datasource.pipeline_obj.destination_cls
        self._destination = None
        self._embedding_generator = None

        if self._destination_cls:
            self._destination = self._destination_cls(**self.datasource.pipeline_obj.destination_data)
            self._destination.initialize_client(datasource=self.datasource)

        if self.datasource.pipeline_obj.embedding:
            embedding_data = self.datasource.pipeline_obj.embedding.data
            embedding_data["additional_kwargs"] = {
                **embedding_data.get("additional_kwargs", {}),
                **{"datasource": self.datasource},
            }
            self._embedding_generator = self.datasource.pipeline_obj.embedding_cls(**embedding_data)

    def search(self, query: str, use_hybrid_search=True, **kwargs) -> List[dict]:
        content_key = self.datasource.destination_text_content_key
        query_embedding = None

        if kwargs.get("search_filters", None):
            raise NotImplementedError("Search filters are not supported for this data source.")

        documents = []

        if self._embedding_generator:
            query_embedding = self._embedding_generator.get_embedding(query)

        if self._destination:
            query_result = self._destination.search(
                query=query,
                use_hybrid_search=use_hybrid_search,
                query_embedding=query_embedding,
                datasource_uuid=str(self.datasource.uuid),
                **kwargs
            )
            documents = list(
                map(
                    lambda x: Document(page_content_key=content_key, page_content=x.text, metadata=x.metadata),
                    query_result.nodes,
                )
            )
        return documents

    def get_entry_text(self, data: dict) -> str:
        documents = [TextNode(metadata={}, text="")]
        node_ids = data.get("document_ids", [])
        if not node_ids:
            node_ids = data.get("nodes", [])

        if self._destination:
            self._destination.initialize_client(datasource=self.datasource)
            if node_ids:
                result = self._destination.get_nodes(node_ids[:20])
                if result:
                    documents = result
        return documents[0].extra_info, "\n".join(list(map(lambda x: x.text, documents)))
