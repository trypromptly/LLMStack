import logging
from typing import Any, NamedTuple

from llmstack.common.utils.liquid import render_template
from llmstack.play.actor import Actor
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
    def __init__(
        self,
        coordinator_urn,
        dependencies,
        template=None,
    ):
        super().__init__(id="output", coordinator_urn=coordinator_urn, dependencies=dependencies)
        self._template = template
        self.reset()

    def input(self, message: Any) -> Any:
        if self._template:
            try:
                self._data = render_template(self._template, message)
            except Exception as e:
                logger.error(
                    f"Error rendering template {self._template} with data {self._data}: {e}",
                )
        else:
            self._data = message
        self._data_done = True
        self._output_stream.finalize()

    def input_stream(self, message: Any) -> Any:
        self._data_chunks.append(message)

    def get_output(self):
        while True:
            if (
                self._error
                or (self._stopped and self._data_sent and not self._data)
                or (self._data_done and self._data_sent)
            ):
                break
            if not self._data or self._data_sent:
                continue

            self._data_sent = True
            yield {"output": self._data, "chunks": self._data_chunks}

        if self._error:
            yield {"errors": list(self._error.values())}

        if self._stopped and not self._data_sent:
            yield {"errors": ["Output interrupted"]}

    def get_output_stream(self):
        while True:
            if self._error or self._stopped or (self._data_done and self._data_chunk_sent):
                break

            if self._data_chunks_sent < len(self._data_chunks):
                self._data_chunk = self._data_chunks[self._data_chunks_sent]
                self._data_chunks_sent += 1
                self._data_chunk_sent = False

            if not self._data_chunk or self._data_chunk_sent:
                continue
            self._data_chunk_sent = True

            yield self._data_chunk

        if self._error:
            yield {"errors": list(self._error.values())}

    def on_stop(self) -> None:
        logger.info("Stopping output actor")
        self._data_done = True
        self._data_chunk_sent = True
        self._stopped = True
        return super().on_stop()

    def on_error(self, error) -> None:
        logger.info(f"Error in output actor: {error}")
        self._error = error
        self._data_done = True
        self._output_stream.finalize()

    def reset(self) -> None:
        logger.info("Resetting output actor")
        self._data = None
        self._data_chunks = []
        self._data_done = False
        self._data_sent = False
        self._data_chunks_sent = 0
        self._data_chunk = None
        self._data_chunk_sent = False
        self._error = None
        self._stopped = False

        super().reset()

    def get_dependencies(self):
        if not self._template:
            return []

        dependencies = [x.split(".")[0] for x in extract_jinja2_variables(self._template)]

        return list(set(dependencies))
