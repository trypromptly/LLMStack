def get_destination_cls(slug, provider_slug):
    from llmstack.data.destinations.vector_stores.chromadb import ChromaDB
    from llmstack.data.destinations.vector_stores.weaviate import Weaviate

    for cls in [ChromaDB, Weaviate]:
        if cls.slug() == slug and cls.provider_slug() == provider_slug:
            return cls
    return None
