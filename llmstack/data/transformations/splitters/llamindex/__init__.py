from llama_index.core.node_parser import (
    CodeSplitter,
    SemanticDoubleMergingSplitterNodeParser,
    SemanticSplitterNodeParser,
    SentenceSplitter,
    SentenceWindowNodeParser,
    TokenTextSplitter,
)

from llmstack.data.transformations.base import BaseTransformation


class LlamIndexSentenceSplitter(BaseTransformation, SentenceSplitter):
    @classmethod
    def slug(cls):
        return "sentence-splitter"

    @classmethod
    def provider_slug(cls):
        return "llamindex"


class LlamIndexCodeSplitter(BaseTransformation, CodeSplitter):
    @classmethod
    def slug(cls):
        return "code-splitter"

    @classmethod
    def provider_slug(cls):
        return "llamindex"


class LlamIndexSemanticSplitterNodeParser(BaseTransformation, SemanticSplitterNodeParser):
    @classmethod
    def slug(cls):
        return "semantic-splitter-node-parser"

    @classmethod
    def provider_slug(cls):
        return "llamindex"


class LlamIndexSemanticDoubleMergingSplitterNodeParser(BaseTransformation, SemanticDoubleMergingSplitterNodeParser):
    @classmethod
    def slug(cls):
        return "semantic-double-merging-splitter-node-parser"

    @classmethod
    def provider_slug(cls):
        return "llamindex"


class LlamIndexSentenceWindowNodeParser(BaseTransformation, SentenceWindowNodeParser):
    @classmethod
    def slug(cls):
        return "sentence-window-node-parser"

    @classmethod
    def provider_slug(cls):
        return "llamindex"


class LlamIndexTokenTextSplitter(BaseTransformation, TokenTextSplitter):
    @classmethod
    def slug(cls):
        return "token-text-splitter"

    @classmethod
    def provider_slug(cls):
        return "llamindex"


__all__ = [
    "LlamIndexSentenceSplitter",
    "LlamIndexCodeSplitter",
    "LlamIndexSemanticSplitterNodeParser",
    "LlamIndexSemanticDoubleMergingSplitterNodeParser",
    "LlamIndexSentenceWindowNodeParser",
    "LlamIndexTokenTextSplitter",
]
