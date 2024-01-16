from typing import Iterator

from pydantic import Field

from llmstack.common.blocks.base.schema import BaseSchema
from llmstack.connections.models import (Connection, ConnectionStatus,
                                         ConnectionType)
from llmstack.connections.types import ConnectionTypeInterface


class ApolloRESTAPIConfiguration(BaseSchema):
    api_key: str = Field(
        description="API Key for Apollo REST API",
        default="",
        widget="password",
    )


class ApolloRESTAPI(ConnectionTypeInterface[ApolloRESTAPIConfiguration]):
    @staticmethod
    def name() -> str:
        return "Apollo REST API"

    @staticmethod
    def provider_slug() -> str:
        return "apollo"

    @staticmethod
    def slug() -> str:
        return "apollo_rest_api"

    @staticmethod
    def description() -> str:
        return "Connect to the Apollo REST API"

    @staticmethod
    def type() -> ConnectionType:
        return ConnectionType.CREDENTIALS

    async def activate(self, connection: Connection) -> Iterator[str]:
        # Verify the key works
        try:
            import requests

            url = "https://api.apollo.io/v1/auth/health"

            querystring = {
                "api_key": connection.configuration["api_key"],
            }

            headers = {
                "Cache-Control": "no-cache",
                "Content-Type": "application/json",
            }

            response = requests.request(
                "GET",
                url,
                headers=headers,
                params=querystring,
            )

            if response.status_code == 200 and response.json()["is_logged_in"]:
                connection.status = ConnectionStatus.ACTIVE
                yield connection
            else:
                connection.status = ConnectionStatus.FAILED
                yield connection

        except Exception as e:
            connection.status = ConnectionStatus.FAILED
            yield {"error": str(e), "connection": connection}
