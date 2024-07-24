import json

from llama_index.core.node_parser import CodeSplitter as _CodeSplitter
from llama_index.core.node_parser import (
    SemanticDoubleMergingSplitterNodeParser as _SemanticDoubleMergingSplitterNodeParser,
)
from llama_index.core.node_parser import (
    SemanticSplitterNodeParser as _SemanticSplitterNodeParser,
)
from llama_index.core.node_parser import SentenceSplitter as _SentenceSplitter
from llama_index.core.node_parser import (
    SentenceWindowNodeParser as _SentenceWindowNodeParser,
)
from llama_index.core.node_parser import TokenTextSplitter as _TokenTextSplitter

from llmstack.common.blocks.base.schema import get_ui_schema_from_json_schema


class LlamaIndexSplitters:
    @classmethod
    def get_schema(cls):
        json_schema = json.loads(cls.schema_json())
        json_schema["properties"].pop("callback_manager", None)
        json_schema["properties"].pop("class_name", None)
        return json_schema

    @classmethod
    def get_ui_schema(cls):
        return get_ui_schema_from_json_schema(cls.get_schema())

    class Config:
        fields = {
            "callback_manager": {"exclude": True},
        }


class SentenceSplitter(_SentenceSplitter, LlamaIndexSplitters):
    @classmethod
    def slug(cls):
        return "sentence-splitter"

    @classmethod
    def provider_slug(cls):
        return "promptly"


class CodeSplitter(_CodeSplitter, LlamaIndexSplitters):
    @classmethod
    def slug(cls):
        return "code-splitter"

    @classmethod
    def provider_slug(cls):
        return "promptly"


class SemanticSplitterNodeParser(_SemanticSplitterNodeParser, LlamaIndexSplitters):
    @classmethod
    def slug(cls):
        return "semantic-splitter-node-parser"

    @classmethod
    def provider_slug(cls):
        return "promptly"


class SemanticDoubleMergingSplitterNodeParser(_SemanticDoubleMergingSplitterNodeParser, LlamaIndexSplitters):
    @classmethod
    def slug(cls):
        return "semantic-double-merging-splitter-node-parser"

    @classmethod
    def provider_slug(cls):
        return "promptly"


class SentenceWindowNodeParser(_SentenceWindowNodeParser, LlamaIndexSplitters):
    @classmethod
    def slug(cls):
        return "sentence-window-node-parser"

    @classmethod
    def provider_slug(cls):
        return "promptly"


class TokenTextSplitter(_TokenTextSplitter, LlamaIndexSplitters):
    @classmethod
    def slug(cls):
        return "token-text-splitter"

    @classmethod
    def provider_slug(cls):
        return "promptly"


__all__ = [
    "SentenceSplitter",
    "CodeSplitter",
    "SemanticSplitterNodeParser",
    "SemanticDoubleMergingSplitterNodeParser",
    "SentenceWindowNodeParser",
    "TokenTextSplitter",
]
