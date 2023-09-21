import logging
import time
from typing import Any
from typing import NamedTuple

from jinja2 import Template

from play.actor import Actor
from play.actor import BookKeepingData
from play.utils import extract_jinja2_variables

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
    def __init__(self, output_stream, dependencies=[], template=None, all_dependencies=[]):
        super().__init__(dependencies=dependencies, all_dependencies=all_dependencies)
        self._output_stream = output_stream
        self._data = None
        self._data_chunk = None
        self._data_chunks = []
        self._data_sent = False
        self._data_chunk_sent = False
        self._data_chunks_sent = 0
        self._data_done = False
        self._template = template
        self._error = None
        self._stopped = False

    def input(self, message: Any) -> Any:
        if self._template:
            try:
                self._data = Template(self._template).render(**message)
            except Exception as e:
                logger.error(
                    f'Error rendering template {self._template} with data {self._data}: {e}',
                )
        else:
            self._data = message
        self._data_done = True
        self._output_stream.finalize()

        output_response = OutputResponse(
            response_content_type='application/json' if not self._template else 'text/markdown',
            response_status=200 if not self._error else 400,
            response_body=self._data if not self._error else self._error,
            response_headers={},
        )

        self._output_stream.bookkeep(
            BookKeepingData(
            run_data={**output_response._asdict()}, timestamp=time.time(),
            ),
        )

    def input_stream(self, message: Any) -> Any:
        self._data_chunks.append(message)

    def get_output(self):
        while True:
            if self._error or self._stopped or (self._data_done and self._data_sent):
                break
            if not self._data or self._data_sent:
                continue
            self._data_sent = True

            yield self._data

        if self._error:
            yield {'errors': list(self._error.values())}

        if self._stopped:
            yield {'errors': ['Timed out waiting for response']}

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
            yield {'errors': list(self._error.values())}

    def on_stop(self) -> None:
        self._data_done = True
        self._data_sent = True
        self._data_chunk_sent = True
        self._stopped = True
        return super().on_stop()

    def on_error(self, error) -> None:
        logger.info(f'Error in output actor: {error}')
        self._error = error
        self._data_done = True
        self._output_stream.finalize()

        output_response = OutputResponse(
            response_content_type='application/json',
            response_status=400,
            response_body=self._error,
            response_headers={},
        )

        self._output_stream.bookkeep(
            BookKeepingData(
            run_data={**output_response._asdict()}, timestamp=time.time(),
            ),
        )

    def get_dependencies(self):
        if not self._template:
            return []

        dependencies = [
            x.split('.')[0]
            for x in extract_jinja2_variables(self._template)
        ]

        return list(set(dependencies))
