import asyncio
import logging
import time
from typing import Any, NamedTuple

from asgiref.sync import async_to_sync

from llmstack.play.actor import Actor, BookKeepingData

logger = logging.getLogger(__name__)


class InputRequest(NamedTuple):
    """
    Input request
    """

    request_endpoint_uuid: str
    request_app_uuid: str
    request_app_session_key: str
    request_owner: object
    request_uuid: str
    request_user_email: str
    request_ip: str
    request_location: str
    request_user_agent: str
    request_content_type: str
    request_body: str
    disable_history: bool = False
    request_app_store_uuid: str = ""


class InputActor(Actor):
    def __init__(
        self,
        coordinator_urn: str,
        bookkeeping_queue: asyncio.Queue = None,
    ):
        super().__init__(
            id="_inputs0",
            coordinator_urn=coordinator_urn,
            dependencies=["coordinator"],
            bookkeeping_queue=bookkeeping_queue,
        )

    def input(self, message: Any) -> Any:
        async_to_sync(self._output_stream.write)(message["coordinator"])
        self._output_stream.finalize()
        self._output_stream.bookkeep(
            BookKeepingData(
                input=message["coordinator"],
                timestamp=time.time(),
            ),
        )
