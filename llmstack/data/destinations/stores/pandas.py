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
    schema: List[SchemaEntry] = Field(
        description="Schema of the table",
        default=[SchemaEntry(name="id", type="string"), SchemaEntry(name="text", type="string")],
    )
    mapping: List[MappingEntry] = Field(
        description="Mapping for the table", default=[MappingEntry(source="text", target="text")]
    )

    _asset = PrivateAttr(default=None)
    _dataframe = PrivateAttr(default=None)
    _name = PrivateAttr(default="pandas")

    @classmethod
    def slug(cls):
        return "pandas"

    @classmethod
    def provider_slug(cls):
        return "promptly"

    def initialize_client(self, *args, **kwargs):
        datasource = kwargs.get("datasource")
        self._name = datasource.name
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
        extra_data = {
            k: v for k, v in document.extra_info.get("extra_data", {}).items() if k in [m.target for m in self.mapping]
        }
        for item in self.schema:
            if item.name == "id" or item.name == "text" or item.name == "embedding":
                continue
            if item.name not in extra_data:
                if item.type == "string":
                    extra_data[item.name] = ""
                elif item.type == "number":
                    extra_data[item.name] = 0
                elif item.type == "boolean":
                    extra_data[item.name] = False
            elif item.name in extra_data:
                if item.type == "number":
                    extra_data[item.name] = float(extra_data[item.name])
                elif item.type == "boolean":
                    extra_data[item.name] = bool(extra_data[item.name])
                extra_data[item.name] = str(extra_data[item.name])

        for node in document.nodes:
            node_metadata = node.metadata
            document_dict = {"text": node.text, "embedding": node.embedding, **extra_data, **node_metadata}
            entry_dict = {
                "id": node.id_,
                **{mapping.source: document_dict.get(mapping.target) for mapping in self.mapping},
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

    def _embedding_search(self, df, query_embedding, limit=10):
        import faiss
        import numpy as np

        df_embeddings = np.array([json.loads(x) for x in df["embedding"]])
        query_embedding_array = np.array(query_embedding)
        index = faiss.IndexFlatL2(df_embeddings.shape[1])
        index.add(df_embeddings)
        # Search for the most similar vectors
        distances, idx = index.search(np.expand_dims(query_embedding_array, axis=0), limit)
        results = pd.DataFrame({"_distances": distances[0], "_ann": idx[0]})
        merged = pd.merge(results, df, left_on="_ann", right_index=True)
        return merged

    def search(self, query: str, **kwargs):
        df = self._dataframe
        if kwargs.get("search_filters"):
            df = df.query(kwargs.get("search_filters"))
        if query and kwargs.get("query_embedding"):
            df = self._embedding_search(df, kwargs.get("query_embedding"), limit=kwargs.get("limit", 10))
        result = df.to_dict(orient="records")
        nodes = []
        for entry in result:
            entry.pop("embedding")
            nodes.append(
                TextNode(
                    text=json.dumps(entry),
                    metadata={"query": query, "source": self._name, "search_filters": kwargs.get("search_filters")},
                )
            )

        node_ids = list(map(lambda x: x["id"], result))
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
                lambda x: TextNode(id_=x["id"], text=json.dumps(x), metadata={"source": self._name}),
                rows.to_dict(orient="records"),
            )
        )
        return []
