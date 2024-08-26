from pydantic import Field

from llmstack.common.blocks.base.schema import BaseSchema
from llmstack.connections.models import ConnectionType
from llmstack.connections.types import ConnectionTypeInterface


class BasicAuthenticationConfiguration(BaseSchema):
    username: str = Field(..., description="The username to use for basic authentication")
    password: str = Field(
        ..., description="The password to use for basic authentication", json_schema_extra={"widget": "password"}
    )


class BasicAuthenticationBasedAPILogin(
    ConnectionTypeInterface[BasicAuthenticationConfiguration],
):
    @staticmethod
    def name() -> str:
        return "Basic Authentication"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    @staticmethod
    def slug() -> str:
        return "basic_authentication"

    @staticmethod
    def description() -> str:
        return "Basic Authentication based API Login"

    @staticmethod
    def type() -> ConnectionType:
        return ConnectionType.CREDENTIALS
