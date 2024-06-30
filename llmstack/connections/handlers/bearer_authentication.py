from pydantic import Field

from llmstack.common.blocks.base.schema import BaseSchema
from llmstack.connections.models import ConnectionType
from llmstack.connections.types import ConnectionTypeInterface


class BearerAuthenticationConfiguration(BaseSchema):
    token: str = Field(json_schema_extra={"widget": "textarea"})
    token_prefix: str = "Bearer"


class BearerAuthenticationBasedAPILogin(
    ConnectionTypeInterface[BearerAuthenticationConfiguration],
):
    @staticmethod
    def name() -> str:
        return "Bearer Authentication"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    @staticmethod
    def slug() -> str:
        return "bearer_authentication"

    @staticmethod
    def description() -> str:
        return "Bearer Token based API authentication"

    @staticmethod
    def type() -> ConnectionType:
        return ConnectionType.CREDENTIALS
