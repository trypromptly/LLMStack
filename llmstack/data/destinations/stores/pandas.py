import base64
import io
import json
import logging
import uuid
from typing import List

import pandas as pd
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores.types import VectorStoreQueryResult
from pydantic import BaseModel, Field, PrivateAttr

from llmstack.data.destinations.base import BaseDestination
from llmstack.data.sources.base import DataDocument

logger = logging.getLogger(__name__)


def create_empty_csv(headers=[]):
    filename = f"pandas_destination_{str(uuid.uuid4())[:4]}.csv"
    empty_str = base64.b64encode(",".join(headers).encode()).decode("utf-8")
    return f"data:text/csv;name={filename};base64,{empty_str}"


def create_destination_document_asset(file, document_id, datasource_uuid):
    from llmstack.data.models import DataSourceEntryFiles

    if not file:
        return None

    file_obj = DataSourceEntryFiles.create_from_data_uri(
        file, ref_id=document_id, metadata={"datasource_uuid": datasource_uuid}
    )
    return file_obj


def get_destination_document_asset_by_document_id(document_id):
    from llmstack.data.models import DataSourceEntryFiles

    file = DataSourceEntryFiles.objects.filter(ref_id=document_id).first()
    return file


class SchemaEntry(BaseModel):
    name: str
    type: str


class MappingEntry(BaseModel):
    source: str
    target: str


class PandasStore(BaseDestination):
    name: str = Field(description="Name of the table")
    schema: List[SchemaEntry] = Field(
        description="Schema of the table",
        default=[SchemaEntry(name="id", type="string"), SchemaEntry(name="text", type="string")],
    )
    mapping: List[MappingEntry] = Field(
        description="Mapping for the table", default=[MappingEntry(source="text", target="text")]
    )

    _asset = PrivateAttr(default=None)
    _dataframe = PrivateAttr(default=None)

    @classmethod
    def slug(cls):
        return "pandas"

    @classmethod
    def provider_slug(cls):
        return "promptly"

    def initialize_client(self, *args, **kwargs):
        datasource = kwargs.get("datasource")
        document_id = str(datasource.uuid)
        asset = get_destination_document_asset_by_document_id(document_id)

        if asset is None:
            file = create_empty_csv(headers=[schema_entry.name for schema_entry in self.schema])
            self._asset = create_destination_document_asset(file, document_id, str(datasource.uuid))
        else:
            self._asset = asset

        file_content = io.BytesIO(self._asset.file.read())
        self._dataframe = pd.read_csv(file_content)

    def add(self, document):
        filename = self._asset.metadata.get("file_name")

        ids = [r.node_id for r in document.nodes]
        for node in document.nodes:
            document_dict = {"text": node.text, **document.extra_info}
            entry_dict = {
                "id": node.id_,
                **{mapping.source: document_dict[mapping.target] for mapping in self.mapping},
            }
            self._dataframe = self._dataframe._append(entry_dict, ignore_index=True)

        buffer = io.BytesIO()
        self._dataframe.to_csv(buffer, index=False)
        buffer.seek(0)
        self._asset.update_file(buffer.getvalue(), filename)
        return ids

    def delete(self, document: DataDocument):
        buffer = io.BytesIO()
        filename = self._asset.metadata.get("file_name")
        for node_id in document.node_ids:
            self._dataframe = self._dataframe[self._dataframe["id"] != node_id]

        buffer = io.BytesIO()
        self._dataframe.to_csv(buffer, index=False)
        buffer.seek(0)
        self._asset.update_file(buffer.getvalue(), filename)

    def search(self, query: str, **kwargs):
        result = self._dataframe.query(query).to_dict(orient="records")
        result_text = json.dumps(result)
        nodes = [TextNode(text=result_text, metadata={"query": query, "source": self.name})]
        node_ids = []
        return VectorStoreQueryResult(nodes=nodes, ids=node_ids, similarities=[])

    def create_collection(self):
        return self._store.create_collection()

    def delete_collection(self):
        if self._asset:
            self._asset.file.delete()
            self._asset.delete()

    def get_nodes(self, node_ids=None, filters=None):
        rows = self._dataframe[self._dataframe["id"].isin(node_ids)]

        return list(
            map(
                lambda x: TextNode(id_=x["id"], text=json.dumps(x), metadata={"source": self.name}),
                rows.to_dict(orient="records"),
            )
        )
        return []
