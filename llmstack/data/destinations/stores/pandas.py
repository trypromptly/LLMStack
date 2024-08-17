import base64
import io
import logging
import uuid
from typing import List

import pandas as pd
from pydantic import BaseModel, Field, PrivateAttr

from llmstack.data.destinations.base import BaseDestination

logger = logging.getLogger(__name__)


def create_empty_csv(headers=[]):
    filename = f"pandas_desctination_{str(uuid.uuid4())[:4]}.csv"
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
        # Add to the pandas dataframe
        document_dict = {"text": document.text, **document.extra_info}
        entry_dict = {
            "id": str(uuid.uuid4()),
            **{mapping.source: document_dict[mapping.target] for mapping in self.mapping},
        }
        logger.info(f"Adding entry to pandas dataframe: {entry_dict}")
        self._dataframe = self._dataframe._append(entry_dict, ignore_index=True)
        logger.info(f"Dataframe shape: {self._dataframe.shape}")
        logger.info(f"Dataframe columns: {self._dataframe.columns}")
        logger.info(f"Dataframe data: {self._dataframe}")
        buffer = io.BytesIO()
        self._dataframe.to_csv(buffer, index=False)
        buffer.seek(0)

        with self._asset.file.open("wb") as f:
            f.write(buffer.getvalue())
        self._asset.save()

    def delete(self, document):
        pass

    def search(self, query: str, **kwargs):
        return self._store.search(query, **kwargs)

    def create_collection(self):
        return self._store.create_collection()

    def delete_collection(self):
        if self._asset:
            self._asset.delete()

    def get_nodes(self, node_ids=None, filters=None):
        return self._store.get_nodes(node_ids=node_ids, filters=filters)
