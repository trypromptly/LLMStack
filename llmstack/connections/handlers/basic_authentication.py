from pydantic import Field
from llmstack.common.blocks.base.schema import BaseSchema
from llmstack.connections.types import ConnectionTypeInterface
from llmstack.connections.models import ConnectionType


class BasicAuthenticationConfiguration(BaseSchema):
    username: str
    password: str


class BasicAuthenticationBasedAPILogin(
        ConnectionTypeInterface[BasicAuthenticationConfiguration]):
    @staticmethod
    def name() -> str:
        return 'Basic Authentication'

    @staticmethod
    def provider_slug() -> str:
        return 'promptly'

    @staticmethod
    def slug() -> str:
        return 'basic_authentication'

    @staticmethod
    def description() -> str:
        return 'Basic Authentication based API Login'

    @staticmethod
    def type() -> ConnectionType:
        return ConnectionType.CREDENTIALS
