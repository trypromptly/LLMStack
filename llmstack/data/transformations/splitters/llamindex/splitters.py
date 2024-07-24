from llama_index.core.node_parser import (
    CodeSplitter,
    SemanticDoubleMergingSplitterNodeParser,
    SemanticSplitterNodeParser,
    SentenceSplitter,
    SentenceWindowNodeParser,
    TokenTextSplitter,
)


class LlamIndexSentenceSplitter(SentenceSplitter):
    @classmethod
    def slug(cls):
        return "sentence-splitter"

    @classmethod
    def provider_slug(cls):
        return "llamindex"


class LlamIndexCodeSplitter(CodeSplitter):
    @classmethod
    def slug(cls):
        return "code-splitter"

    @classmethod
    def provider_slug(cls):
        return "llamindex"


class LlamIndexSemanticSplitterNodeParser(SemanticSplitterNodeParser):
    @classmethod
    def slug(cls):
        return "semantic-splitter-node-parser"

    @classmethod
    def provider_slug(cls):
        return "llamindex"


class LlamIndexSemanticDoubleMergingSplitterNodeParser(SemanticDoubleMergingSplitterNodeParser):
    @classmethod
    def slug(cls):
        return "semantic-double-merging-splitter-node-parser"

    @classmethod
    def provider_slug(cls):
        return "llamindex"


class LlamIndexSentenceWindowNodeParser(SentenceWindowNodeParser):
    @classmethod
    def slug(cls):
        return "sentence-window-node-parser"

    @classmethod
    def provider_slug(cls):
        return "llamindex"


class LlamIndexTokenTextSplitter(TokenTextSplitter):
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
