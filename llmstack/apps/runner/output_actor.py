import asyncio
import logging
from typing import Any, Dict, List, NamedTuple

import pykka
from diff_match_patch import diff_match_patch
from pydantic import BaseModel

from llmstack.common.utils.liquid import render_template
from llmstack.play.actor import Actor
from llmstack.play.messages import Error, Message, MessageType
from llmstack.play.output_stream import stitch_model_objects

logger = logging.getLogger(__name__)

SENTINEL = object()


class OutputResponse(NamedTuple):
    """
    Output response
    """

    response_content_type: str
    response_status: int
    response_body: str
    response_headers: dict


class OutputActor(Actor):
    def __init__(
        self,
        coordinator_urn,
        dependencies,
        templates: Dict[str, str] = {},
    ):
        super().__init__(id="output", coordinator_urn=coordinator_urn, dependencies=dependencies)
        self._templates = templates
        self.reset()
        self._diff_match_patch = diff_match_patch()

    def on_receive(self, message: Message) -> Any:
        if message.type == MessageType.ERRORS:
            self.on_error(message.sender, message.data.errors)
            return

        if message.type == MessageType.CONTENT_STREAM_CHUNK:
            try:
                self._stitched_data = stitch_model_objects(self._stitched_data, {message.sender: message.data.chunk})
                new_int_output = render_template(self._templates["output"], self._stitched_data)
                delta = self._diff_match_patch.diff_toDelta(
                    self._diff_match_patch.diff_main(self._int_output.get("output", ""), new_int_output)
                )
                self._int_output["output"] = new_int_output

                self._content_queue.put_nowait(
                    {
                        "deltas": {"output": delta},
                        "chunk": {message.sender: message.data.chunk},
                    }
                )
            except Exception as e:
                logger.error(f"Error processing content stream chunk: {e}")

        if message.type == MessageType.CONTENT:
            self._messages[message.sender] = (
                message.data.content.model_dump()
                if isinstance(message.data.content, BaseModel)
                else message.data.content
            )

            if set(self._dependencies) == set(self._messages.keys()):
                self._content_queue.put_nowait(
                    {
                        "output": self._int_output,
                        "chunks": self._messages,
                    }
                )

        if message.type == MessageType.BOOKKEEPING:
            self._bookkeeping_data_map[message.sender] = message.data

            if set(self._dependencies).issubset(self._bookkeeping_data_map.keys()):
                self._bookkeeping_data_future.set(self._bookkeeping_data_map)

    async def get_output(self):
        try:
            while True:
                if not self._content_queue.empty():
                    output = self._content_queue.get_nowait()
                    yield output
                    self._content_queue.task_done()
                else:
                    if self._errors or self._stopped:
                        break
                    await asyncio.sleep(0.01)

        except asyncio.CancelledError:
            logger.info("Output stream cancelled")
        finally:
            if self._errors:
                yield {"errors": [error.message for error in self._errors]}
            elif self._stopped:
                yield {"errors": ["Output interrupted"]}

    def on_stop(self) -> None:
        self._stopped = True
        return super().on_stop()

    def on_error(self, sender, errors: List[Error]) -> None:
        logger.error(f"Error in output actor: {errors}")
        self._errors = errors

    def reset(self) -> None:
        self._stitched_data = {}
        self._int_output = {}
        self._errors = None
        self._stopped = False
        self._bookkeeping_data_map = {}
        self._bookkeeping_data_future = pykka.ThreadingFuture()
        self._content_queue = asyncio.Queue()
        self._messages = {}
        super().reset()

    def get_bookkeeping_data(self):
        return self._bookkeeping_data_future
