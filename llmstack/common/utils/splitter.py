import csv
import logging
import re
from abc import ABC, abstractmethod
from io import StringIO
from typing import Any, Callable, Iterable, List, Optional

import spacy
import tiktoken
from unstructured.chunking.basic import chunk_elements
from unstructured.partition.auto import partition, partition_text

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
        separate_length = self._length_function(separator)
        chunksList = []
        cur_chunk: List[str] = []
        total_length = 0

        for chunk in strs:
            chunk_length = self._length_function(chunk)
            max_length = total_length + chunk_length + separate_length

            # Check if the length exceed the maximum chunk size
            if max_length > self._chunk_size:
                if cur_chunk:
                    combined_chunk = separator.join(cur_chunk)
                    if combined_chunk:
                        chunksList.append(combined_chunk)

                    # Adjust total length and current chunk
                    while total_length > self._chunk_overlap or (max_length > self._chunk_size and total_length > 0):
                        total_length -= len(cur_chunk[0]) + separate_length
                        cur_chunk.pop(0)

            cur_chunk.append(chunk)
            total_length += chunk_length + separate_length

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
    def num_tokens_from_string_using_tiktoken(
        cls,
        string: str,
        encoding_name: str = "cl100k_base",
    ) -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens

    @classmethod
    def num_tokens_for_string_using_gpt3_approximation(
        cls,
        string: str,
    ) -> int:
        """Returns the number of tokens in a text string. Source: https://platform.openai.com/tokenizer"""
        return max(len(string) // 4, 1)


class CharacterTextSplitter(TextSplitter):
    """Split text into chunks of specified maximum size and overlap."""

    def __init__(
        self,
        separator: str = "\n",
        is_regex: bool = False,
        **kwargs: Any,
    ) -> None:
        """Create a new TextSplitter."""
        super().__init__(**kwargs)
        self._separator = separator
        self._is_regex = is_regex
        self._keep_separator = True

    # Split a given text with a given separator using regex, and return a list
    # of chunks
    def _split_text_with_regex(
        self,
        text: str,
        separator: str,
        keep_separator: bool,
    ) -> List[str]:
        if keep_separator:
            chunks = re.split(f"({separator})", text)
        else:
            chunks = re.split(separator, text)
        return chunks

    def split_text(self, text: str) -> List[str]:
        separator = self._separator if self._is_regex else re.escape(self._separator)
        splits = self._split_text_with_regex(
            text,
            separator,
            self._keep_separator,
        )
        return self._merge_chunks(splits, separator=self._separator)


class CSVTextSplitter(TextSplitter):
    """Split CSV document into chunks of specified maximum size and overlap."""

    def split_text(self, text: str) -> List[str]:
        chunks = []
        file_handle = StringIO(text)
        csv_reader = csv.DictReader(file_handle)
        for i, row in enumerate(csv_reader):
            content = "\n\n".join(f"{k}: {v}" for k, v in row.items())
            chunks.append(content)
        return chunks


def _make_spacy_pipeline_for_splitting(pipeline: str):
    if pipeline == "sentencizer":
        from spacy.lang.en import English

        sentencizer = English()
        sentencizer.add_pipe("sentencizer")
    else:
        sentencizer = spacy.load(pipeline, disable=["ner"])
    return sentencizer


class SpacyTextSplitter(TextSplitter):
    """Split Text using Spacy"""

    def __init__(
        self,
        separator: str = "\n\n",
        pipeline: str = "sentencizer",
        length_func=len,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._length_function = length_func
        self._tokenizer = _make_spacy_pipeline_for_splitting(pipeline)
        self._separator = separator

    def split_text(self, text: str) -> List[str]:
        self._tokenizer(text)
        sentences = (s.text.strip() for s in self._tokenizer(text).sents)
        return self._merge_chunks(sentences, self._separator)


class HtmlSplitter(TextSplitter):
    def __init__(
        self,
        chunk_size: int = 500,
        length_function: Any = len,
        non_breaking_tags=["ul", "ol", "a", "li", "p", "h1", "h2", "h3", "h4", "h5", "h6", "img"],
        **kwargs,
    ):
        self._keep_script = kwargs.get("keep_script", True)
        self._non_breaking_tags = non_breaking_tags
        super().__init__(chunk_size, chunk_overlap=0, length_function=length_function)

    def _split_html(self, element):
        from bs4 import Comment

        if self._length_function(str(element)) <= self._chunk_size:
            return [str(element)]

        if element.name in self._non_breaking_tags:
            return [str(element)]

        if isinstance(element, Comment):
            return [str(element)]

        chunks = []
        parent_tags = None

        if len(list(element.children)):
            parent_tags = str(element).split("".join([str(child) for child in element.children]))
            if len(parent_tags) != 2:
                raise Exception("Error in processing HTML")
            chunks.append(parent_tags[0])

        for child in element.children:
            if child.name:
                chunks.extend(self._split_html(child))
            else:
                chunks.append(str(child))

        if parent_tags:
            chunks.append(parent_tags[1])

        return chunks

    def split_text(self, text: str) -> List[str]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(text, "html.parser")
        html_chunks = self._split_html(soup)
        return self._merge_chunks(html_chunks, separator="")


class UnstructuredTextSplitter(TextSplitter):
    """Interface for splitting unstructured text into structured data."""

    def __init__(
        self,
        chunking_stragy: str = "by_title",  # supported 'basic' or 'by_title'
        chunk_size: int = 4000,
        length_function: Any = len,
    ):
        self._chunking_strategy = chunking_stragy
        super().__init__(chunk_size, chunk_overlap=0, length_function=length_function)

    def _split_text(self, text: str) -> List[str]:
        elements = partition_text(
            text=text,
            chunking_strategy=self._chunking_strategy,
            skip_infer_table_types="[]",  # don't forget to include apostrophe around the square bracket
        )
        chunks = chunk_elements(elements, max_characters=self._chunk_size)
        return [chunk.text for chunk in chunks]

    def split_text(self, text: str) -> List[str]:
        chunks = self._split_text(text)
        return self._merge_chunks(chunks, separator="")


class UnstructuredDocumentSplitter(TextSplitter):
    """Interface for splitting unstructured text into structured data."""

    def __init__(
        self,
        file_name: str,
        chunking_strategy: str = "by_title",  # supported 'basic' or 'by_title'
        chunk_size: int = 4000,
        length_function: Any = len,
    ):
        self._file_name = file_name
        self._chunking_strategy = chunking_strategy
        super().__init__(chunk_size, chunk_overlap=0, length_function=length_function)

    def _split_text(self) -> List[str]:
        elements = partition(
            filename=self._file_name,
            chunking_strategy=self._chunking_strategy,
            skip_infer_table_types="[]",  # don't forget to include apostrophe around the square bracket
        )
        chunks = chunk_elements(elements, max_characters=self._chunk_size)
        return [chunk.text for chunk in chunks]

    def split_text(self) -> List[str]:
        chunks = self._split_text()
        return self._merge_chunks(chunks, separator="")
