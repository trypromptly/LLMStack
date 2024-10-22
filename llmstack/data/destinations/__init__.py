from functools import cache

from llmstack.data.destinations.stores.pandas import PandasStore
from llmstack.data.destinations.stores.postgres import PostgresDatabase
from llmstack.data.destinations.stores.singlestore import SingleStore
from llmstack.data.destinations.vector_stores.chromadb import ChromaDB
from llmstack.data.destinations.vector_stores.pinecone import Pinecone
from llmstack.data.destinations.vector_stores.qdrant import Qdrant
from llmstack.data.destinations.vector_stores.vector_store import PromptlyVectorStore
from llmstack.data.destinations.vector_stores.weaviate import Weaviate


@cache
def get_destination_cls(slug, provider_slug):
    for cls in [ChromaDB, Weaviate, SingleStore, Pinecone, Qdrant, PromptlyVectorStore, PandasStore, PostgresDatabase]:
        if cls.slug() == slug and cls.provider_slug() == provider_slug:
            return cls
    return None


__all__ = ["SingleStore", "Pinecone", "Weaviate", "PandasStore", "PostgresDatabase"]
