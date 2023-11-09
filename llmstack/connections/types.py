from enum import Enum
from typing import Generic, Iterator, TypeVar

from llmstack.common.utils.module_loader import get_all_sub_classes
from llmstack.connections.models import Connection, ConnectionActivationInput

class ConnectionType(str, Enum):
    BROWSER_LOGIN = 'browser_login'
    OAUTH2 = 'oauth2'
    CREDENTIALS = 'credentials'

def get_connection_type_interface_subclasses():
    subclasses = []
    allowed_packages = [
        'llmstack.connections.handlers',
    ]

    excluded_packages = []

    try:
        import jnpr.junos
    except:
        excluded_packages.append('llmstack.connections.handlers.junos_login')

    for package in allowed_packages:
        subclasses_in_package = get_all_sub_classes(
            package, ConnectionTypeInterface)

        for subclass in subclasses_in_package:
            if subclass.__module__ not in excluded_packages:
                subclasses.append(subclass)

    return subclasses


ConnectionConfigurationSchemaType = TypeVar(
    'ConnectionConfigurationSchemaType')
class ConnectionTypeInterface(Generic[ConnectionConfigurationSchemaType]):
    """Interface for connection types."""
    @staticmethod
    def slug() -> str:
        raise NotImplementedError

    @staticmethod
    def provider_slug() -> str:
        raise NotImplementedError

    @staticmethod
    def name() -> str:
        raise NotImplementedError

    @staticmethod
    def description() -> str:
        raise NotImplementedError
    
    @staticmethod
    def connection_type() -> ConnectionType:
        raise NotImplementedError
    
    @staticmethod
    def metadata() -> dict:
        return {}

    @classmethod
    def parse_config(cls, config: dict) -> ConnectionConfigurationSchemaType:
        connection_type_interface = cls.__orig_bases__[0]
        return connection_type_interface.__args__[0].parse_obj(config)

    async def activate(self, connection: Connection) -> Iterator[str]:
        # Establish connection and persist any connection artifacts
        raise NotImplementedError

    def input(self, activation_input: ConnectionActivationInput) -> None:
        # Input data from the user
        pass

    @classmethod
    def get_config_schema(cls) -> ConnectionConfigurationSchemaType:
        connection_type_interface = cls.__orig_bases__[0]
        return connection_type_interface.__args__[0].get_schema()

    @classmethod
    def get_config_ui_schema(cls) -> dict:
        connection_type_interface = cls.__orig_bases__[0]
        return connection_type_interface.__args__[0].get_ui_schema()


class ConnectionTypeFactory:
    """
    Factory class for Data source types
    """
    @staticmethod
    def get_connection_type_handler(connection_type_slug, provider_slug) -> ConnectionTypeInterface:
        subclasses = get_connection_type_interface_subclasses()
        for subclass in subclasses:
            # Convert to lowercase to avoid case sensitivity
            if subclass.slug() == connection_type_slug and subclass.provider_slug() == provider_slug:
                return subclass
        return None
