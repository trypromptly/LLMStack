from functools import cache

from llmstack.data.transformations.llamindex.embeddings_generator import (
    EmbeddingsGenerator,
)
from llmstack.data.transformations.llamindex.splitters import (
    CodeSplitter,
    SemanticDoubleMergingSplitterNodeParser,
    SemanticSplitterNodeParser,
    SentenceSplitter,
    SentenceWindowNodeParser,
    TokenTextSplitter,
)
from llmstack.data.transformations.splitters import CSVTextSplitter
from llmstack.data.transformations.unstructured.splitters import UnstructuredIOSplitter


@cache
def get_transformer_cls(slug, provider_slug):
    for cls in [UnstructuredIOSplitter, EmbeddingsGenerator, CSVTextSplitter]:
        if cls.slug() == slug and cls.provider_slug() == provider_slug:
            return cls

    return None


__all__ = [
    "CodeSplitter",
    "SemanticDoubleMergingSplitterNodeParser",
    "SemanticSplitterNodeParser",
    "SentenceSplitter",
    "SentenceWindowNodeParser",
    "TokenTextSplitter",
    "CSVTextSplitter",
    "UnstructuredIOSplitter",
    "EmbeddingsGenerator",
]
