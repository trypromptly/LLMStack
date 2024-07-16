from llama_index.core.vector_stores.types import BasePydanticVectorStore

from llmstack.data.destinations.base import BaseDestination


class VectorStoreConfiguration(BaseDestination):
    pass

    def initialize_client(self, *args, **kwargs) -> BasePydanticVectorStore:
        raise NotImplementedError
