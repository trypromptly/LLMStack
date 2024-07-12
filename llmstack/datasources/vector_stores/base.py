from llama_index.core.vector_stores.types import BasePydanticVectorStore
from pydantic import BaseModel


class VectorStoreConfiguration(BaseModel):
    pass

    def initialize_client(self, *args, **kwargs) -> BasePydanticVectorStore:
        raise NotImplementedError
