import json
from typing import Optional

from pydantic import Field, PrivateAttr

from llmstack.common.utils.prequests import post
from llmstack.data.destinations.base import BaseDestination
from llmstack.processors.providers.singlestore import SinglestoreProviderConfig


class SingleStore(BaseDestination):
    database: str = Field(description="Database name")
    deployment_name: Optional[str] = Field(description="Deployment name", default="*")

    _deployment_config: Optional[SinglestoreProviderConfig] = PrivateAttr()

    @classmethod
    def slug(cls):
        return "singlestore"

    @classmethod
    def provider_slug(cls):
        return "singlestore"

    def initialize_client(self, *args, **kwargs):
        datasource = kwargs.get("datasource")
        self._deployment_config = datasource.profile.get_provider_config(
            model_slug=self.slug(), deployment_key=self.deployment_name, provider_slug=self.provider_slug()
        )

    def search(self, query: str, **kwargs):
        url = f"{self._deployment_config.host}/api/v2/query/rows"
        headers = {
            "Accept": "application/json",
        }
        data = {
            "sql": query,
            "database": self.database,
            "program_name": "promptly_datasource",
        }
        response = post(
            url,
            headers=headers,
            data=json.dumps(data),
            auth=(
                self._deployment_config.username,
                self._deployment_config.password,
            ),
        )
        response.raise_for_status()
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

        return [csv_result]
