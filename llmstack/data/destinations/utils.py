def get_source_cls(slug, provider_slug):
    from llmstack.data.destinations.vector_stores.legacy_chromadb import (
        PromptlyLegacyChromaDBVectorStoreConfiguration,
    )
    from llmstack.data.destinations.vector_stores.legacy_weaviate import (
        PromptlyLegacyWeaviateVectorStoreConfiguration,
    )

    for cls in [PromptlyLegacyWeaviateVectorStoreConfiguration, PromptlyLegacyChromaDBVectorStoreConfiguration]:
        if cls.slug() == slug and cls.provider_slug() == provider_slug:
            return cls

    return None
