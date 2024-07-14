from typing import Annotated, Union

from pydantic import Field

from llmstack.data.destinations.vector_stores.legacy_chromadb import (
    PromptlyLegacyChromaDBVectorStoreConfiguration,
)
from llmstack.data.destinations.vector_stores.legacy_weaviate import (
    PromptlyLegacyWeaviateVectorStoreConfiguration,
)

VectorStore = Annotated[
    Union[PromptlyLegacyWeaviateVectorStoreConfiguration, PromptlyLegacyChromaDBVectorStoreConfiguration],
    Field(discriminator="type"),
]


def get_vector_store_configuration(data):
    if data["type"] == "promptly_legacy_weaviate":
        return PromptlyLegacyWeaviateVectorStoreConfiguration(**data)
    elif data["type"] == "promptly_legacy_chromadb":
        return PromptlyLegacyChromaDBVectorStoreConfiguration(**data)

    raise NotImplementedError(f"Unknown vector store type: {data['type']}")
