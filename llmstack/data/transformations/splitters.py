import csv
import json
import logging
from typing import List, Optional

from llama_index.core.bridge.pydantic import Field
from llama_index.core.node_parser.interface import TextSplitter

from llmstack.assets.utils import get_asset_by_objref
from llmstack.common.blocks.base.schema import get_ui_schema_from_json_schema

logger = logging.getLogger(__name__)


class PromptlyTransformers:
    @classmethod
    def get_schema(cls):
        json_schema = cls.schema()
        json_schema["properties"].pop("callback_manager", None)
        json_schema["properties"].pop("class_name", None)
        json_schema["properties"].pop("include_metadata", None)
        json_schema["properties"].pop("include_prev_next_rel", None)
        return json_schema

    @classmethod
    def get_ui_schema(cls):
        return get_ui_schema_from_json_schema(cls.get_schema())

    @classmethod
    def get_default_data(cls):
        data = cls().dict()
        data.pop("callback_manager", None)
        data.pop("class_name", None)
        data.pop("include_metadata", None)
        data.pop("include_prev_next_rel", None)
        return data


class CSVTextSplitter(TextSplitter, PromptlyTransformers):
    exclude_columns: Optional[List[str]] = Field(
        default=None,
        description="Columns to drop from the csv row",
    )
    text_columns: Optional[List[str]] = Field(
        default=None,
        description="Columns to include in the text",
    )
    metadata_prefix: Optional[str] = Field(
        default="cts_",
        description="Prefix for metadata columns",
    )

    @classmethod
    def slug(cls):
        return "csv-text-splitter"

    @classmethod
    def provider_slug(cls):
        return "promptly"

    def split_text(self, text: str) -> List[str]:
        raise NotImplementedError

    def split_texts(self, texts: List[str]) -> List[str]:
        raise NotImplementedError

    def _parse_nodes(self, nodes, show_progress: bool = False, **kwargs):
        from llama_index.core.node_parser.node_utils import build_nodes_from_splits
        from llama_index.core.utils import get_tqdm_iterable

        all_nodes = []
        nodes_with_progress = get_tqdm_iterable(nodes, show_progress, "Parsing nodes")
        for node in nodes_with_progress:
            if hasattr(node, "content"):
                asset = get_asset_by_objref(node.content, None, None)
                with asset.file.open(mode="r") as f:
                    csv_reader = csv.DictReader(f)
                    for row in csv_reader:
                        content = {}
                        for column_name, value in row.items():
                            if self.exclude_columns and column_name in self.exclude_columns:
                                continue
                            content[column_name] = value
                        row_text = json.dumps(content)
                        if self.text_columns:
                            if len(self.text_columns) == 1:
                                row_text = content[self.text_columns[0]]
                            else:
                                text_parts = {}
                                for column_name in self.text_columns:
                                    text_parts[column_name] = content.get(column_name, "")
                                row_text = json.dumps(text_parts)
                        all_nodes.extend(build_nodes_from_splits([row_text], node, id_func=self.id_func))
                        for column_name, value in content.items():
                            metadata_key = f"{self.metadata_prefix}{column_name}".replace(" ", "_")
                            all_nodes[-1].metadata[metadata_key] = value

        return all_nodes
