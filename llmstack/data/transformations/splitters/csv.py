import csv
from io import StringIO
from typing import List, Optional

from llama_index.core.node_parser.interface import MetadataAwareTextSplitter
from pydantic import Field


class CSVTextSplitter(MetadataAwareTextSplitter):
    include_columns: Optional[List[str]] = Field(
        default=None,
        description="Columns to include in the text",
    )
    exclude_columns: Optional[List[str]] = Field(
        default=None,
        description="Columns to exclude from the text",
    )

    @classmethod
    def slug(cls):
        return "csv-text-splitter"

    @classmethod
    def provider_slug(cls):
        return "promptly"

    @classmethod
    def class_name(cls) -> str:
        return "CSVTextSplitter"

    def _split_text(self, text: str) -> List[str]:
        chunks = []
        file_handle = StringIO(text)
        csv_reader = csv.DictReader(file_handle)
        for i, row in enumerate(csv_reader):
            content = ""
            for column_name, value in row.items():
                if self.include_columns and column_name not in self.include_columns:
                    continue
                if self.exclude_columns and column_name in self.exclude_columns:
                    continue
                content += f"{column_name}: {value}\n"
            chunks.append(content)
        return chunks

    def split_text_metadata_aware(self, text: str, metadata_str: str) -> List[str]:
        return self._split_text(text)

    def split_text(self, text: str) -> List[str]:
        return self._split_text(text)
