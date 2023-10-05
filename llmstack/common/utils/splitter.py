import csv
import logging
from abc import ABC
from abc import abstractmethod
from io import StringIO
import re
from typing import Any, Callable, Iterable
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

class CharacterTextSplitter(TextSplitter):
    """Split text into chunks of specified maximum size and overlap."""
    
    def __init__(
        self, separator: str = "\n", is_regex: bool = False, **kwargs: Any
    ) -> None:
        """Create a new TextSplitter."""
        super().__init__(**kwargs)
        self._separator = separator
        self._is_regex = is_regex
        self._keep_separator = True

    # Split a given text with a given separator using regex, and return a list of chunks
    def _split_text_with_regex(self, text: str, separator: str, keep_separator: bool) -> List[str]:
        if keep_separator:
            chunks = re.split(f'({separator})', text)
        else:
            chunks = re.split(separator, text)
        return chunks 
    
    def split_text(self, text: str) -> List[str]:
        separator = (
            self._separator if self._is_regex else re.escape(self._separator)
        )
        splits = self._split_text_with_regex(text, separator, self._keep_separator)
        return self._merge_chunks(splits, separator=self._separator)

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
    

class HtmlSplitter(TextSplitter):
    def __init__(self, chunk_size: int = 500, length_function: Any = len, **kwargs):
        self._keep_script = kwargs.get('keep_script', True)
        self._is_html_fragment = kwargs.get('is_html_fragment', False)
        super().__init__(chunk_size, chunk_overlap=0, length_function=length_function)
    
    def _merge_list_elements(self, elements, n):
        # Merge elements into chunks of size n or less
        chunks = []
        current_chunk = ""
        for element in elements:
            if len(current_chunk) + len(element) <= n:
                current_chunk += element
            else:
                chunks.append(current_chunk)
                current_chunk = element
        if len(current_chunk) > 0:
            chunks.append(current_chunk)
        
        return chunks
    
    def _get_html_elements_recursive(self, element, max_length):
        import lxml
        if element.tag == lxml.etree.Comment:
            return [lxml.html.tostring(element).decode('utf-8')]
        
        # If string representation of element is less than max_length, return it        
        attribute_list = []
        for k,v in element.items():
            if '\"' in v:
                attribute_list.append(f"{k}={v}")
            else:
                attribute_list.append(f"{k}=\"{v}\"")
            
        # Append opening tag with attributes
        attributes = " ".join(attribute_list)
        
        html_elements = [f"<{element.tag} {attributes}>"] if len(attributes) > 0 else [f"<{element.tag}>"]
        
        html_elements.append(element.text or '')
        # Recursively iterate through children
        child_html_elements = []
        for child in element.iterchildren():
            child_elements = self._get_html_elements_recursive(child, max_length)
            if len(''.join(child_elements)) <= max_length:
                child_elements = [''.join(child_elements)]
            child_html_elements += child_elements
        
        if len(''.join(child_html_elements)) <= max_length:
            html_elements = [html_elements[0], html_elements[1], ''.join(child_html_elements)]
        else:
            for e in child_html_elements:
                html_elements.append(e)
        html_elements.append(f"</{element.tag}>")
        html_elements.append(element.tail or '')
        return html_elements
    
    
    def split_text(self, text: str) -> List[str]:
        import lxml.html
        import lxml.etree
        if self._is_html_fragment:
            result = []
            for fragment in lxml.html.fragments_fromstring(text):
                result.extend(self._get_html_elements_recursive(fragment, self._chunk_size))
            
            return self._merge_list_elements(result, self._chunk_size)
        else:
            return self._get_html_elements_recursive(lxml.html.fromstring(text), self._chunk_size)