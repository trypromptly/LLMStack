import logging
from typing import Iterator

from pykka import ThreadingActor

from llmstack.connections.models import (Connection, ConnectionActivationInput,
                                         ConnectionStatus)
from llmstack.connections.types import ConnectionTypeFactory

logger = logging.getLogger(__name__)


class ConnectionActivationActor(ThreadingActor):
    def __init__(self, user, connection_id):
        super().__init__()

        self.connection_id = connection_id
        self.user = user
        self.connection_handler = None

    def on_receive(self, message):
        pass

    def set_connection(self, connection):
        from llmstack.base.models import Profile

        profile = Profile.objects.get(user=self.user)
        profile.add_connection(connection.dict())

    def activate(self) -> Iterator[str]:
        from llmstack.base.models import Profile

        profile = Profile.objects.get(user=self.user)
        connection_obj = (
            profile.get_connection(
                self.connection_id,
            )
            if profile
            else None
        )

        if not profile or not connection_obj:
            raise Exception("Connection not found")

        connection = Connection(**connection_obj)

        self.connection_handler = ConnectionTypeFactory.get_connection_type_handler(
            connection.connection_type_slug,
            connection.provider_slug,
        )()

        connection.status = ConnectionStatus.CONNECTING
        profile.add_connection(connection.dict())

        return self.connection_handler.activate(connection)

    def input(self, activation_input: ConnectionActivationInput):
        return (
            self.connection_handler.input(
                activation_input,
            )
            if self.connection_handler
            else None
        )
