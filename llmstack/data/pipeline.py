import logging
from typing import List, Optional

from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.schema import Document as LlamaDocument

from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.data.models import DataSource
from llmstack.data.schemas import DataDocument

logger = logging.getLogger(__name__)


class LlamaDocumentShim(LlamaDocument):
    text_objref: Optional[str] = None
    content: Optional[str] = None
    mimetype: str = "text/plain"


class DataIngestionPipeline:
    def __init__(self, datasource: DataSource):
        self.datasource = datasource
        self._source_cls = self.datasource.pipeline_obj.source_cls
        self._destination_cls = self.datasource.pipeline_obj.destination_cls
        logger.debug("Initializing DataIngestionPipeline")

        self._destination = None
        self._transformations = self.datasource.pipeline_obj.transformation_objs
        embedding_cls = self.datasource.pipeline_obj.embedding_cls
        if embedding_cls:
            logger.debug("Initializing DataIngestionPipeline Transformation")
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
            logger.debug("Finished Initializing DataIngestionPipeline Transformation")

        if self._destination_cls:
            logger.debug("Initializing DataIngestionPipeline Destination")
            self._destination = self._destination_cls(**self.datasource.pipeline_obj.destination_data)
            self._destination.initialize_client(datasource=self.datasource, create_collection=True)
            logger.debug("Finished Initializing DataIngestionPipeline Destination")

    def process(self, document: DataDocument) -> DataDocument:
        logger.debug(f"Processing document: {document.name}")
        document = self._source_cls.process_document(document)
        logger.debug(f"Creating IngestionPipeline for document: {document.name}")
        ingestion_pipeline = IngestionPipeline(transformations=self._transformations)
        ldoc = LlamaDocumentShim(**document.model_dump())
        ldoc.metadata = {**ldoc.metadata, **document.metadata}
        logger.debug(f"Running IngestionPipeline for document: {document.name}")
        document.nodes = ingestion_pipeline.run(documents=[ldoc])
        logger.debug(f"Finished running IngestionPipeline for document: {document.name}")
        document.node_ids = list(map(lambda x: x.id_, document.nodes))
        if self._destination:
            logger.debug(f"Adding document: {document.name} to destination")
            self._destination.add(document=document)
            logger.debug(f"Finished adding document: {document.name} to destination")

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
        logger.debug("Initializing DataQueryPipeline")

        if self._destination_cls:
            logger.debug("Initializing DataQueryPipeline Destination")
            self._destination = self._destination_cls(**self.datasource.pipeline_obj.destination_data)
            self._destination.initialize_client(datasource=self.datasource, create_collection=False)
            logger.debug("Finished Initializing DataQueryPipeline Destination")

        if self.datasource.pipeline_obj.embedding:
            logger.debug("Initializing DataQueryPipeline Embedding")
            embedding_data = self.datasource.pipeline_obj.embedding.data
            embedding_data["additional_kwargs"] = {
                **embedding_data.get("additional_kwargs", {}),
                **{"datasource": self.datasource},
            }
            self._embedding_generator = self.datasource.pipeline_obj.embedding_cls(**embedding_data)
            logger.debug("Finished Initializing DataQueryPipeline Embedding")

    def search(self, query: str, use_hybrid_search=True, **kwargs) -> List[dict]:
        content_key = self.datasource.destination_text_content_key
        query_embedding = None

        logger.debug(f"Initializing Search for query: {query}")

        if kwargs.get("search_filters", None):
            raise NotImplementedError("Search filters are not supported for this data source.")

        documents = []

        if self._embedding_generator:
            logger.debug("Generating embedding for query")
            query_embedding = self._embedding_generator.get_embedding(query)
            logger.debug("Finished generating embedding for query")

        if self._destination:
            logger.debug(f"Searching for query: {query} in destination")
            query_result = self._destination.search(
                query=query,
                use_hybrid_search=use_hybrid_search,
                query_embedding=query_embedding,
                datasource_uuid=str(self.datasource.uuid),
                **kwargs,
            )
            logger.debug(f"Received results for query: {query} from destination")
            documents = list(
                map(
                    lambda x: Document(page_content_key=content_key, page_content=x.text, metadata=x.metadata),
                    query_result.nodes,
                )
            )
        return documents

    def get_entry_text(self, document: DataDocument) -> str:
        if self._destination:
            if document.node_ids:
                result = self._destination.get_nodes(document.node_ids[:20])
                if result:
                    documents = result
                    return documents[0].extra_info, "\n".join(list(map(lambda x: x.text, documents)))

        return {}, ""
