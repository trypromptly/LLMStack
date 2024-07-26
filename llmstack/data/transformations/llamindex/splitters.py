from typing import Dict, List, Optional

from llama_index.core.bridge.pydantic import BaseModel, Field
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

from llmstack.data.transformations.llamindex.base import LlamaIndexTransformers


class SentenceSplitter(_SentenceSplitter, LlamaIndexTransformers):
    @classmethod
    def slug(cls):
        return "sentence-splitter"

    @classmethod
    def provider_slug(cls):
        return "promptly"


class CodeSplitter(_CodeSplitter, LlamaIndexTransformers):
    @classmethod
    def slug(cls):
        return "code-splitter"

    @classmethod
    def provider_slug(cls):
        return "promptly"


class SemanticSplitterNodeParser(_SemanticSplitterNodeParser, LlamaIndexTransformers):
    @classmethod
    def slug(cls):
        return "semantic-splitter-node-parser"

    @classmethod
    def provider_slug(cls):
        return "promptly"


class LanguageConfig(BaseModel):
    language: Optional[str] = Field(default="english")
    spacy_model: Optional[str] = Field(default="en_core_web_sm")
    model_validation: Optional[bool] = Field(default=True)
    nlp: Optional[Dict] = Field(default=None)
    stopwords: List[str] = Field(default=[])

    def load_model(self) -> None:
        try:
            import spacy
            from nltk.corpus import stopwords
        except ImportError:
            raise ImportError("Spacy is not installed, please install it with `pip install spacy`.")
        self.nlp = spacy.load(self.spacy_model)
        self.stopwords = set(stopwords.words(self.language))


class SemanticDoubleMergingSplitterNodeParser(_SemanticDoubleMergingSplitterNodeParser, LlamaIndexTransformers):
    language_config: LanguageConfig = LanguageConfig()
    max_chunk_size: int = Field(
        default=1500,
        description="Maximum length of chunk that can be subjected to verification (number of characters)",
    )

    @classmethod
    def slug(cls):
        return "semantic-double-merging-splitter-node-parser"

    @classmethod
    def provider_slug(cls):
        return "promptly"


class SentenceWindowNodeParser(_SentenceWindowNodeParser, LlamaIndexTransformers):
    @classmethod
    def slug(cls):
        return "sentence-window-node-parser"

    @classmethod
    def provider_slug(cls):
        return "promptly"


class TokenTextSplitter(_TokenTextSplitter, LlamaIndexTransformers):
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
