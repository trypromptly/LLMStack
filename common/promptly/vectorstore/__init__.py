from abc import ABC
from abc import abstractmethod
from collections import namedtuple
from typing import Any
from typing import List
from typing import Tuple

Document = namedtuple(
    'Document', ['page_content_key', 'page_content', 'metadata', 'embeddings'], defaults=(None, None, None, None),
)

DocumentQuery = namedtuple(
    'DocumentQuery', ['query', 'page_content_key', 'limit', 'metadata', 'search_filters', 'alpha'], defaults=(None, None, 10, None, None, 0.75),
)


class VectorStoreInterface(ABC):
    def __init__(self) -> None:
        self._client = None

    @ property
    def client(self):
        return self._client

    @ abstractmethod
    def add_text(self, index_name: str, document: Document, **kwargs: Any):
        pass

    @ abstractmethod
    def add_texts(self, index_name: str, documents: List[Document], **kwargs: Any):
        pass

    @ abstractmethod
    def get_or_create_index(self, index_name: str, schema: str, **kwargs: Any):
        pass

    @ abstractmethod
    def create_index(self, index_name: str, **kwargs: Any):
        pass

    @ abstractmethod
    def delete_index(self, index_name: str, **kwargs: Any):
        pass

    @ abstractmethod
    def delete_document(self, document_id: str, **kwargs: Any):
        raise NotImplementedError

    @ abstractmethod
    def similarity_search(self, index_name: str, document_query: DocumentQuery, **kwargs) -> List[Tuple[int, float]]:
        raise NotImplementedError

    @abstractmethod
    def hybrid_search(self, index_name: str, document_query: DocumentQuery, **kwargs) -> List[Tuple[int, float]]:
        raise NotImplementedError
