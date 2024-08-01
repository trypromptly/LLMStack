import io
import logging
from typing import List, Optional, Union

from llama_index.core.bridge.pydantic import BaseModel, Field
from llama_index.core.node_parser.interface import TextSplitter
from unstructured.chunking.basic import chunk_elements
from unstructured.chunking.title import chunk_by_title
from unstructured.partition.auto import partition, partition_text

from llmstack.assets.utils import get_asset_by_objref
from llmstack.data.transformations.unstructured.base import UnstructuredIOTransformers

logger = logging.getLogger(__name__)


class ByTitle(BaseModel):
    multipage_sections: Optional[bool] = None
    max_characters: Optional[int] = 1000
    combine_text_under_n_chars: Optional[int] = None
    new_after_n_chars: Optional[int] = None
    overlap: Optional[int] = None
    overlap_all: Optional[bool] = None


class Basic(BaseModel):
    max_characters: Optional[int] = 1000
    new_after_n_chars: Optional[int] = None
    overlap: Optional[int] = None
    overlap_all: Optional[bool] = None


class UnstructuredIOSplitter(TextSplitter, UnstructuredIOTransformers):
    strategy: Optional[Union[Basic, ByTitle]] = Field(
        default=Basic(), description="Strategy to perform document splitting"
    )

    @classmethod
    def slug(cls):
        return "splitter"

    @classmethod
    def provider_slug(cls):
        return "unstructured"

    def split_text(self, node) -> List[str]:
        node_elements = []
        chunks = []

        try:
            if hasattr(node, "content"):
                asset = get_asset_by_objref(node.content, None, None)
                with asset.file.open(mode="rb") as f:
                    asset_file_bytes = f.read()
                    node_elements = partition(
                        file=io.BytesIO(asset_file_bytes),
                        file_name=asset.metadata.get("file_name", ""),
                        content_type=node.mimetype,
                    )
        except Exception:
            pass
        if not node_elements:
            node_elements = partition_text(text=node.get_content() or "")

        if isinstance(self.strategy, ByTitle):
            chunks = chunk_by_title(node_elements, **self.strategy.dict())
        else:
            chunks = chunk_elements(node_elements, **self.strategy.dict())

        return [str(chunk) for chunk in chunks]

    def split_texts(self, texts: List[str]) -> List[str]:
        raise NotImplementedError

    def _parse_nodes(self, nodes, show_progress: bool = False, **kwargs):
        from llama_index.core.node_parser.node_utils import build_nodes_from_splits
        from llama_index.core.utils import get_tqdm_iterable

        all_nodes = []
        nodes_with_progress = get_tqdm_iterable(nodes, show_progress, "Parsing nodes")
        for node in nodes_with_progress:
            splits = self.split_text(node)

            all_nodes.extend(build_nodes_from_splits(splits, node, id_func=self.id_func))

        return all_nodes
