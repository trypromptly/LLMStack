from typing import Any, Iterator, TypeVar

from openai import AsyncStream, Stream

_T = TypeVar("_T")


class LLMRestStream(Stream):
    pass


class LLMGRPCStream(Stream):
    def __init__(
        self,
        *,
        cast_to: type[_T],
        response: Any,
        client: Any,
        process_data: Any,
    ) -> None:
        self.response = response
        self._cast_to = cast_to
        self._client = client
        self._iterator = self.__stream__()
        self._process_data = process_data

    def __next__(self) -> _T:
        return self._iterator.__next__()

    def __iter__(self) -> Iterator[_T]:
        for item in self._iterator:
            yield item

    def _iter_events(self) -> Iterator[Any]:
        for _ in self.response:
            yield _

    def __stream__(self) -> Iterator[_T]:
        iterator = self._iter_events()

        for entry in iterator:
            yield self._process_data(chunk=entry)

        for _entry in iterator:
            ...

    def __enter__(self):
        return self

    def close(self) -> None:
        """
        Close the response and release the connection.

        Automatically called if the response body is read to completion.
        """
        pass


class LLMAsyncStream(AsyncStream):
    pass
