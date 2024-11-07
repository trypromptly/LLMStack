import base64
import io
import json
import logging
import os
import sqlite3
import uuid
from typing import List, Literal, Optional, Union

from llama_index.core.schema import TextNode
from llama_index.core.vector_stores.types import VectorStoreQueryResult
from pydantic import BaseModel, Field, PrivateAttr

from llmstack.data.destinations.base import BaseDestination
from llmstack.data.sources.base import DataDocument

logger = logging.getLogger(__name__)


def create_empty_sqlite_db():
    filename = f"sqlite_{str(uuid.uuid4())[:4]}.db"
    return f"data:application/octet-stream;name={filename};base64,{base64.b64encode(b'').decode('utf-8')}"


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


def create_temp_file_from_asset(asset):
    import tempfile

    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(asset.file.read())
    temp_file.flush()
    temp_file.seek(0)
    return temp_file.name


def get_sqlite_data_type(_type: str):
    if _type == "string":
        return "TEXT"
    elif _type == "number":
        return "REAL"
    elif _type == "boolean":
        return "BOOLEAN"
    return "TEXT"


class SchemaEntry(BaseModel):
    name: str
    type: Union[Literal["string"], Literal["number"], Literal["boolean"]] = "string"


class MappingEntry(BaseModel):
    source: str
    target: str


class FullTextSearchPlugin(BaseModel):
    type: Literal["fts5"] = "fts5"


def load_database_from_asset(asset):
    local_db = create_temp_file_from_asset(asset)
    conn = sqlite3.connect(local_db)
    return conn, local_db


def update_asset_from_database(asset, database):
    # Read the database content
    buffer = io.BytesIO()
    with open(database, "rb") as f:
        buffer.write(f.read())
    buffer.seek(0)
    asset.update_file(buffer.getvalue(), asset.metadata.get("file_name"))
    # Delete the temporary file
    os.remove(database)


class SqliteDatabase(BaseDestination):
    schema: List[SchemaEntry] = Field(
        description="Schema of the table",
        default=[
            SchemaEntry(name="id", type="string"),
            SchemaEntry(name="text", type="string"),
            SchemaEntry(name="metadata_json", type="string"),
        ],
    )
    table_name: str = Field(description="Name of the table", default="data")
    search_plugin: Optional[Union[FullTextSearchPlugin]] = Field(
        description="Search plugin to use",
        default=None,
    )

    _asset = PrivateAttr(default=None)
    _name = PrivateAttr(default="sqlite")

    @classmethod
    def slug(cls):
        return "sqlite"

    @classmethod
    def provider_slug(cls):
        return "promptly"

    def initialize_client(self, *args, **kwargs):
        datasource = kwargs.get("datasource")
        self._name = datasource.name
        document_id = str(datasource.uuid)
        asset = get_destination_document_asset_by_document_id(document_id)

        if asset is None:
            file = create_empty_sqlite_db()
            self._asset = create_destination_document_asset(file, document_id, str(datasource.uuid))
        else:
            self._asset = asset

    def add(self, document):
        conn, local_db = load_database_from_asset(self._asset)
        c = conn.cursor()

        create_table_query = f"CREATE TABLE IF NOT EXISTS {self.table_name} ({','.join([f'{item.name} {get_sqlite_data_type(item.type)}' for item in self.schema])})"
        if self.search_plugin:
            if self.search_plugin.type == "fts5":
                create_table_query = f"CREATE VIRTUAL TABLE IF NOT EXISTS {self.table_name} USING fts5({','.join([f'{item.name}' for item in self.schema])})"
            elif self.search_plugin.type == "semantic":
                import sqlite_vec

                conn.enable_load_extension(True)
                sqlite_vec.load(conn)
                conn.enable_load_extension(False)

                create_table_query = f"CREATE VIRTUAL TABLE IF NOT EXISTS {self.table_name} USING vec0({','.join([f'{item.name} {get_sqlite_data_type(item.type)}' for item in self.schema])}, embedding float[1536])"

        c.execute(create_table_query)

        try:
            for node in document.nodes:
                document_dict = {"text": node.text, "metadata_json": json.dumps(node.metadata)}
                for schema_entry in self.schema:
                    if schema_entry.name == "id" or schema_entry.name == "text" or schema_entry.name == "metadata_json":
                        continue
                    if schema_entry.name in node.metadata:
                        document_dict[schema_entry.name] = node.metadata[schema_entry.name]
                if self.search_plugin and self.search_plugin.type == "semantic":
                    document_dict["embedding"] = node.embedding

                entry_dict = {"id": node.id_, **document_dict}
                c.execute(
                    f"INSERT INTO {self.table_name} ({','.join(entry_dict.keys())}) VALUES ({','.join(['?'] * len(entry_dict))})",
                    list(entry_dict.values()),
                )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.exception(f"Error adding nodes to sqlite store {e}")
            raise e

        update_asset_from_database(self._asset, local_db)
        ids = [r.node_id for r in document.nodes]
        return ids

    def delete(self, document: DataDocument):
        conn, local_db = load_database_from_asset(self._asset)
        c = conn.cursor()
        for node_id in document.node_ids:
            c.execute(f"DELETE FROM {self.table_name} WHERE id = ?", (node_id,))
        conn.commit()
        conn.close()
        update_asset_from_database(self._asset, local_db)

    def search(self, query: str, **kwargs):
        conn, _ = load_database_from_asset(self._asset)
        c = conn.cursor()
        result = c.execute(query).fetchall()
        conn.close()
        nodes = list(
            map(lambda x: TextNode(text=json.dumps(x), metadata={"query": query, "source": self._name}), result)
        )
        node_ids = list(map(lambda x: x, enumerate(result)))
        return VectorStoreQueryResult(nodes=nodes, ids=node_ids, similarities=[])

    def create_collection(self):
        pass

    def delete_collection(self):
        if self._asset:
            self._asset.file.delete()
            self._asset.delete()

    def get_nodes(self, node_ids=None, filters=None):
        conn, _ = load_database_from_asset(self._asset)
        column_names = [schema_entry.name for schema_entry in self.schema]
        c = conn.cursor()
        if node_ids:
            query = f"SELECT {','.join(column_names)} FROM {self.table_name} WHERE id IN ({','.join(['?'] * len(node_ids))})"
            rows = c.execute(query, node_ids).fetchall()
        else:
            rows = c.execute(f"SELECT * FROM {self.table_name}").fetchall()
        conn.close()
        if rows:
            return list(
                map(
                    lambda x: TextNode(id_=x[0], text=json.dumps(x), metadata={"source": self._name}),
                    rows,
                )
            )
        return []
