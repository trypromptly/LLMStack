import json
from typing import Dict, List, Optional

from pydantic import Field

from llmstack.common.blocks.base.schema import BaseSchema
from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.common.utils.models import Config
from llmstack.common.utils.prequests import post
from llmstack.data.models import DataSource
from llmstack.data.sources.datasource_processor import (
    DataSourceProcessor,
    DataSourceSchema,
)


class SingleStoreConnection(BaseSchema):
    host: str = Field(description="Host of the SingleStore instance")
    port: int = Field(
        description="Port number to connect to the SingleStore instance",
    )
    username: str = Field(description="SingleStore username")
    password: str = Field(description="SingleStore password")
    database: str = Field(description="SingleStore database name")


class SingleStoreDatabaseSchema(DataSourceSchema):
    connection: Optional[SingleStoreConnection] = Field(
        default=None,
        description="SingleStore connection details",
    )


class SingleStoreConnectionConfiguration(Config):
    config_type: str = "singlestore_connection"
    is_encrypted: bool = True
    singlestore_config: Optional[Dict] = None


class SingleStoreDataSource(DataSourceProcessor[SingleStoreDatabaseSchema]):
    def __init__(self, datasource: DataSource):
        self.datasource = datasource
        if self.datasource.config and "data" in self.datasource.config:
            config_dict = SingleStoreConnectionConfiguration().from_dict(
                self.datasource.config,
                self.datasource.profile.decrypt_value,
            )
            self._configuration = SingleStoreDatabaseSchema(
                **config_dict["singlestore_config"],
            )
        self._source_name = self.datasource.name

    @staticmethod
    def name() -> str:
        return "Single Store"

    @staticmethod
    def slug() -> str:
        return "singlestore"

    @staticmethod
    def description() -> str:
        return "Single Store is a distributed SQL database that can be deployed anywhere."

    @staticmethod
    def provider_slug() -> str:
        return "singlestore"

    @classmethod
    def is_external(cls) -> bool:
        return True

    @staticmethod
    def process_validate_config(
        config_data: dict,
        datasource: DataSource,
    ) -> dict:
        return SingleStoreConnectionConfiguration(
            singlestore_config=config_data,
        ).to_dict(
            encrypt_fn=datasource.profile.encrypt_value,
        )

    def validate_and_process(self, data: dict):
        raise NotImplementedError

    def get_data_documents(self, data: dict):
        raise NotImplementedError

    def add_entry(self, data: dict):
        raise NotImplementedError

    def _sql_search(self, query: str, **kwargs):
        if self._configuration.connection.host.startswith("https"):
            url = f"{self._configuration.connection.host}/api/v2/query/rows"
        else:
            url = f"https://{self._configuration.connection.host}/api/v2/query/rows"

        headers = {
            "Accept": "application/json",
        }
        data = {
            "sql": query,
            "database": self._configuration.connection.database,
            "program_name": "promptly_datasource",
        }

        response = post(
            url,
            headers=headers,
            data=json.dumps(data),
            auth=(
                self._configuration.connection.username,
                self._configuration.connection.password,
            ),
        )
        response.raise_for_status()
        # JSON to csv
        csv_result = ""
        if "results" in response.json():
            if len(response.json()["results"]) > 0 and "rows" in response.json()["results"][0]:
                rows = response.json()["results"][0]["rows"]
                if len(rows) > 0:
                    csv_result += (
                        ",".join(
                            list(
                                map(
                                    lambda entry: str(entry),
                                    rows[0].keys(),
                                ),
                            ),
                        )
                        + "\n"
                    )
                    for row in rows:
                        csv_result += (
                            ",".join(
                                list(
                                    map(
                                        lambda entry: str(entry),
                                        row.values(),
                                    ),
                                ),
                            )
                            + "\n"
                        )

        return [
            Document(
                page_content_key="content",
                page_content=csv_result,
                metadata={
                    "score": 0,
                    "source": self._source_name,
                },
            ),
        ]

    def similarity_search(self, query: str, **kwargs) -> List[dict]:
        return self._sql_search(query, **kwargs)

    def hybrid_search(self, query: str, **kwargs) -> List[dict]:
        return self._sql_search(query, **kwargs)

    def delete_entry(self, data: dict):
        raise NotImplementedError

    def resync_entry(self, data: dict):
        raise NotImplementedError

    def delete_all_entries(self):
        raise NotImplementedError

    def get_entry_text(self, data: dict) -> str:
        return None, "External Datasource does not support entry text"
