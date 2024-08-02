from functools import cache


@cache
def get_transformer_cls(slug, provider_slug):
    from llmstack.data.transformations import UnstructuredIOSplitter
    from llmstack.data.transformations.llamindex.embeddings_generator import (
        EmbeddingsGenerator,
    )

    for cls in [
        UnstructuredIOSplitter,
        EmbeddingsGenerator,
    ]:
        if cls.slug() == slug and cls.provider_slug() == provider_slug:
            return cls

    return None
