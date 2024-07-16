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
