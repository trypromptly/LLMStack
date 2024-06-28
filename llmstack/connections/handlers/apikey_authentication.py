from typing import Optional

from pydantic import Field

from llmstack.common.blocks.base.schema import BaseSchema
from llmstack.connections.models import ConnectionType
from llmstack.connections.types import ConnectionTypeInterface


class APIKeyAuthenticationConfiguration(BaseSchema):
    api_key: str = Field(
        json_schema_extra={"widget": "password"},
        description="Paste your API Key here",
    )
    header_key: Optional[str] = Field(
        description="Key to use in Header for API Key authentication. This is Optional",
        default=None,
    )


class APIKeyAuthenticationBasedAPILogin(
    ConnectionTypeInterface[APIKeyAuthenticationConfiguration],
):
    @staticmethod
    def name() -> str:
        return "API Key Authentication"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    @staticmethod
    def slug() -> str:
        return "api_key_authentication"

    @staticmethod
    def description() -> str:
        return "API Key based API authentication"

    @staticmethod
    def type() -> ConnectionType:
        return ConnectionType.CREDENTIALS
