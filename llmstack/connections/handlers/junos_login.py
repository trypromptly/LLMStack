from typing import Iterator, Union

from pydantic import Field

from llmstack.connections.models import (Connection, ConnectionStatus,
                                         ConnectionType)
from llmstack.connections.types import ConnectionTypeInterface

from .web_login import WebLoginBaseConfiguration


class JunosLoginConfiguration(WebLoginBaseConfiguration):
    address: str = Field(
        default="localhost",
        description="Address of the device",
    )
    username: str = Field(description="Username for the device")
    password: str = Field(
        description="Password for the account",
        widget="password",
    )


class JunosLogin(ConnectionTypeInterface[JunosLoginConfiguration]):
    @staticmethod
    def name() -> str:
        return "Junos Login"

    @staticmethod
    def provider_slug() -> str:
        return "juniper"

    @staticmethod
    def slug() -> str:
        return "junos_login"

    @staticmethod
    def description() -> str:
        return "Login to a Junos Device"

    @staticmethod
    def type() -> ConnectionType:
        return ConnectionType.CREDENTIALS

    async def activate(self, connection) -> Iterator[Union[Connection, dict]]:
        try:
            from jnpr.junos import Device

            device = Device(
                host=connection.configuration["address"],
                user=connection.configuration["username"],
                password=connection.configuration["password"],
            ).open()
            device.close()

            connection.status = ConnectionStatus.ACTIVE
            yield connection
        except Exception as e:
            connection.status = ConnectionStatus.FAILED
            yield {"error": str(e), "connection": connection}
