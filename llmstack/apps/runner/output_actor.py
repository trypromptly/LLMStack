import asyncio
import logging
from typing import Any, Dict, NamedTuple

import pykka
from diff_match_patch import diff_match_patch
from pydantic import BaseModel

from llmstack.common.utils.liquid import render_template
from llmstack.play.actor import Actor
from llmstack.play.messages import Message, MessageType
from llmstack.play.output_stream import stitch_model_objects
from llmstack.play.utils import extract_jinja2_variables

logger = logging.getLogger(__name__)


class OutputResponse(NamedTuple):
    """
    Output response
    """

    response_content_type: str
    response_status: int
    response_body: str
    response_headers: dict


class OutputActor(Actor):
    """
    This will write to a channel by topic name session_id/request_id. app_runner will listen on this so the consumer can receive response for this specific message
    """

    def __init__(
        self,
        coordinator_urn,
        dependencies,
        templates: Dict[str, str] = {},
    ):
        super().__init__(id="output", coordinator_urn=coordinator_urn, dependencies=dependencies)
        self._templates = templates
        self.reset()  # Initialize internal state
        self._diff_match_patch = diff_match_patch()

    def on_receive(self, message: Message) -> Any:
        if message.type == MessageType.ERRORS:
            self.on_error(message.sender, message.data.errors)
            return

        if message.type == MessageType.CONTENT_STREAM_BEGIN:
            pass

        if message.type == MessageType.CONTENT_STREAM_END:
            pass

        if message.type == MessageType.CONTENT_STREAM_CHUNK:
            # We will try to stitch whatever data is available, render the template and return the diff
            try:
                self._stitched_data = stitch_model_objects(self._stitched_data, {message.sender: message.data.chunk})
                new_int_output = render_template(self._templates["output"], self._stitched_data)
                delta = self._diff_match_patch.diff_toDelta(
                    self._diff_match_patch.diff_main(self._int_output.get("output", ""), new_int_output)
                )
                self._int_output["output"] = new_int_output
                # logger.info(f"DELTA: {delta} --- {new_int_output}")

                self._delta_chunks.append({"output": delta})
                self._data_chunk = {message.sender: message.data.chunk}
                self._data_chunks.append({message.sender: message.data.chunk})
            except Exception as e:
                logger.error(e)

        if message.type == MessageType.CONTENT:
            logger.info(f"GOT CONTENT: {message}")
            self._messages = {
                **self._messages,
                **{
                    message.sender: (
                        message.data.content.model_dump()
                        if isinstance(message.data.content, BaseModel)
                        else message.data.content
                    )
                },
            }

            if set(self._dependencies) == set(self._messages.keys()):
                if self._templates and "output" in self._templates:
                    try:
                        self._data = render_template(self._templates["output"], self._messages)
                    except Exception as e:
                        logger.error(
                            f"Error rendering template {self._templates['output']} with data {self._data}: {e}",
                        )
                else:
                    self._data = self._messages
                self._data_done = True

        # Handle bookkeeping
        if message.type == MessageType.BOOKKEEPING:
            self._bookkeeping_data_map[message.sender] = message.data

            if set(self._dependencies) == set(self._bookkeeping_data_map.keys()):
                self._bookkeeping_data_future.set(self._bookkeeping_data_map)

    async def get_output(self):
        while True:
            if (
                self._error
                or (self._stopped and self._data_sent and not self._data)
                or (self._data_done and self._data_sent)
            ):
                break
            if not self._data or self._data_sent:
                await asyncio.sleep(0.001)
                continue

            self._data_sent = True
            return {"output": self._data, "chunks": self._data_chunks}

        if self._error:
            return {"errors": list(self._error.values())}

        if self._stopped and not self._data_sent:
            return {"errors": ["Output interrupted"]}

    async def get_output_stream(self):
        while True:
            if self._error or self._stopped:
                break

            if self._data_chunks_sent_index < len(self._data_chunks):
                self._data_chunk = self._data_chunks[self._data_chunks_sent_index]
                self._data_chunks_sent_index += 1
                self._data_chunk_sent = False

                yield {"deltas": self._delta_chunks[self._data_chunks_sent_index - 1], "chunk": self._data_chunk}
                self._data_chunk_sent = True
            elif self._data_done:
                yield {
                    "chunks": self._messages,
                    "output": self._int_output,
                }
                break
            else:
                await asyncio.sleep(0.0001)

        if self._error:
            yield {"errors": list(self._error.values())}

    def on_stop(self) -> None:
        logger.info("Stopping output actor")
        self._data_done = True
        self._data_chunk_sent = True
        self._stopped = True
        return super().on_stop()

    def on_error(self, sender, error) -> None:
        logger.info(f"Error in output actor: {error}")
        self._error = error
        self._data_done = True
        self._output_stream.finalize()

    def reset(self) -> None:
        logger.info("Resetting output actor")
        self._data = None
        self._stitched_data = {}
        self._int_output = {}
        self._data_done = False
        self._data_sent = False
        self._data_chunks_sent_index = 0
        self._data_chunk = None
        self._data_chunks = []
        self._data_chunk_sent = False
        self._delta_chunks = []
        self._delta_chunk_sent = False
        self._error = None
        self._stopped = False
        self._bookkeeping_data_map = {}
        self._bookkeeping_data_future = pykka.ThreadingFuture()

        super().reset()

    def get_bookkeeping_data(self):
        return self._bookkeeping_data_future

    def get_dependencies(self):
        if not self._template:
            return []

        dependencies = [x.split(".")[0] for x in extract_jinja2_variables(self._template)]

        return list(set(dependencies))
