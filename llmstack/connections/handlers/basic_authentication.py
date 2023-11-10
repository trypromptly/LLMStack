from llmstack.common.blocks.base.schema import BaseSchema
from llmstack.connections.types import ConnectionType, ConnectionTypeInterface

class BasicAuthenticationConfiguration(BaseSchema):
    username: str
    password: str
    
class BasicAuthenticationBasedAPILogin(ConnectionTypeInterface[BasicAuthenticationConfiguration]):
    @staticmethod
    def name() -> str:
        return 'Basic Authentication'

    @staticmethod
    def provider_slug() -> str:
        return 'promptly'

    @staticmethod
    def slug() -> str:
        return 'username_password_api'

    @staticmethod
    def description() -> str:
        return 'Username Password based API Login'
    
    @staticmethod
    def type() -> ConnectionType:
        return ConnectionType.CREDENTIALS