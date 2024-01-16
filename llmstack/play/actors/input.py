import logging
import time
from types import TracebackType
from typing import Any
from typing import NamedTuple
from typing import Type

from asgiref.sync import async_to_sync
from pydantic import BaseModel

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


class InputActor(Actor):
    def __init__(
            self,
            output_stream,
            input_request,
            dependencies=[],
            all_dependencies=[]):
        super().__init__(dependencies=dependencies, all_dependencies=all_dependencies)
        self.input_request = input_request
        self.data = None
        self.output_stream = output_stream
        self.stream_started = False
        self.stream_closed = False
        self.sent_data = False

    def write(self, message: Any) -> Any:
        async_to_sync(self.output_stream.write)(message)
        self.output_stream.finalize()
        self.output_stream.bookkeep(
            BookKeepingData(
                input=message,
                run_data={
                    **self.input_request._asdict()},
                timestamp=time.time(),
            ),
        )

    def get_output(self):
        # Return an iter that yield whenever we get a new message
        while True:
            if not self.stream_started or self.sent_data and not self.stream_closed:
                continue

            self.sent_data = True

            if self.stream_closed:
                break

            yield self.data.__dict__

    def on_stop(self) -> None:
        pass

    def on_failure(
            self,
            exception_type: Type[BaseException],
            exception_value: BaseException,
            traceback: TracebackType) -> None:
        logger.error(
            f'IOActor failed: {exception_type} {exception_value} {traceback}',
        )
