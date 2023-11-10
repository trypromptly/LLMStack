from pydantic import Field
from llmstack.common.blocks.base.schema import BaseSchema
from llmstack.connections.types import ConnectionType, ConnectionTypeInterface

class BearerAuthenticationConfiguration(BaseSchema):
    connection_type_slug: str = Field(default='bearer_authentication', widget='hidden')
    token: str = Field(widget='textarea')
    token_prefix: str = 'Bearer'
    
class BearerAuthenticationBasedAPILogin(ConnectionTypeInterface[BearerAuthenticationConfiguration]):
    @staticmethod
    def name() -> str:
        return 'Bearer Authentication'

    @staticmethod
    def provider_slug() -> str:
        return 'promptly'

    @staticmethod
    def slug() -> str:
        return 'bearer_authentication'

    @staticmethod
    def description() -> str:
        return 'Bearer Token based API authentication'
    
    @staticmethod
    def type() -> ConnectionType:
        return ConnectionType.CREDENTIALS