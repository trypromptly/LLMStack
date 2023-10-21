from pydantic import Field
from llmstack.connections.types import BaseSchema, ConnectionTypeInterface


class WebLoginBaseConfiguration(BaseSchema):
    _storage_state: str = Field(
        description='Storage state', widget='textarea', hidden=True)


class WebLoginConfiguration(WebLoginBaseConfiguration):
    url: str = Field(description='URL to login to')
    username: str = Field(description='Username')
    password: str = Field(description='Password', widget='password')


class WebLogin(ConnectionTypeInterface[WebLoginConfiguration]):
    @staticmethod
    def name() -> str:
        return 'Web Login'

    @staticmethod
    def provider_slug() -> str:
        return 'promptly'

    @staticmethod
    def slug() -> str:
        return 'web_login'

    @staticmethod
    def description() -> str:
        return 'Login to a website'
