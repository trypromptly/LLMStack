import csv
import logging
from abc import ABC
from abc import abstractmethod
from io import StringIO
from typing import Callable, Iterable
from typing import List
from typing import Optional

import tiktoken
import spacy

logger = logging.getLogger(__name__)


class TextSplitter(ABC):
    """Interface for splitting text into chunks."""

    def __init__(
        self,
        chunk_size: int = 4000,
        chunk_overlap: int = 200,
        length_function: Optional[Callable[[str], int]] = None,
    ):
        """Create a new TextSplitter."""
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._length_function = length_function or len

    
    def _merge_chunks(self, strs: Iterable[str], separator: str) -> List[str]:
        separate_length =  self._length_function(separator)
        chunksList = []
        cur_chunk: List[str] = []
        total_length = 0

        for chunk in strs:
            chunk_length =  self._length_function(chunk)
            max_length = total_length + chunk_length + separate_length
            
            # Check if the length exceed the maximum chunk size
            if max_length > self._chunk_size:
                if cur_chunk:
                    combined_chunk = separator.join(cur_chunk)
                    if combined_chunk:
                        chunksList.append(combined_chunk)

                    # Adjust total length and current chunk
                    while total_length > self._chunk_overlap or (max_length > self._chunk_size and total_length > 0):
                        total_length -= (len(cur_chunk[0]) + separate_length)
                        cur_chunk.pop(0)

            cur_chunk.append(chunk)
            total_length += (chunk_length + separate_length)

        # Handle the last piece if there's any
        if cur_chunk:
            combined_chunk = separator.join(cur_chunk)
            if combined_chunk:
                chunksList.append(combined_chunk)

        return chunksList

    @abstractmethod
    def split_text(self, text: str) -> List[str]:
        """Split text into multiple components."""

    @classmethod
    def num_tokens_from_string_using_tiktoken(cls, string: str, encoding_name: str = 'cl100k_base') -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens

    @classmethod
    def num_tokens_for_string_using_gpt3_approximation(cls, string: str) -> int:
        """Returns the number of tokens in a text string. Source: https://platform.openai.com/tokenizer"""
        return max(len(string) // 4, 1)


class CSVTextSplitter(TextSplitter):
    """Split CSV document into chunks of specified maximum size and overlap."""

    def split_text(self, text: str) -> List[str]:
        chunks = []
        file_handle = StringIO(text)
        csv_reader = csv.DictReader(file_handle)
        for i, row in enumerate(csv_reader):
            content = '\n\n'.join(f'{k}: {v}' for k, v in row.items())
            chunks.append(content)
        return chunks


def _make_spacy_pipeline_for_splitting(pipeline: str):
    if pipeline == 'sentencizer':
        from spacy.lang.en import English

        sentencizer = English()
        sentencizer.add_pipe('sentencizer')
    else:
        sentencizer = spacy.load(pipeline, disable=['ner'])
    return sentencizer


class SpacyTextSplitter(TextSplitter):
    """Split Text using Spacy"""

    def __init__(self, separator: str = '\n\n', pipeline: str = 'sentencizer', length_func=len, **kwargs):
        super().__init__(**kwargs)
        self._length_function = length_func
        self._tokenizer = _make_spacy_pipeline_for_splitting(pipeline)
        self._separator = separator

    def split_text(self, text: str) -> List[str]:
        self._tokenizer(text)
        sentences = (s.text.strip() for s in self._tokenizer(text).sents)
        return self._merge_chunks(sentences, self._separator)