from typing import Annotated, Union

from pydantic import Field

from llmstack.data.vector_stores.chromadb import ChromaDBVectorStoreConfiguration
from llmstack.data.vector_stores.legacy_weaviate import (
    PromptlyLegacyWeaviateVectorStoreConfiguration,
)

VectorStore = Annotated[
    Union[PromptlyLegacyWeaviateVectorStoreConfiguration, ChromaDBVectorStoreConfiguration],
    Field(discriminator="type"),
]


def get_vector_store_configuration(data):
    if data["type"] == "promptly_legacy_weaviate":
        return PromptlyLegacyWeaviateVectorStoreConfiguration(**data)
    elif data["type"] == "chromadb":
        return ChromaDBVectorStoreConfiguration(**data)

    raise NotImplementedError(f"Unknown vector store type: {data['type']}")
