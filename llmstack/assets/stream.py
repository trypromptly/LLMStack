import logging

from django_redis import get_redis_connection

from llmstack.assets.models import Assets

logger = logging.getLogger(__name__)

objref_stream_client = get_redis_connection("objref_stream")


class AssetStream:
    """
    Helper class to manage streaming assets.
    """

    def __init__(self, asset: Assets):
        self._asset = asset
        self._id = 0

    @property
    def objref(self) -> str:
        return self._asset.objref

    def get_asset(self):
        return self._asset

    def append_chunk(self, chunk: bytes):
        if chunk == b"":
            return

        objref_stream_client.xadd(
            self.objref,
            {"chunk": chunk, "id": self._id},
        )
        self._id += 1

        # Expire the stream after 20 minutes
        objref_stream_client.expire(self.objref, 1200)

    def finalize(self):
        # Read the stream and finalize the asset
        file_bytes = b""

        message_index = 0
        while True:
            stream = objref_stream_client.xread(count=10, streams={self.objref: message_index})
            if not stream:
                break

            for _, messages in stream:
                for id, message in messages:
                    file_bytes += message[b"chunk"]
                    message_index = id

        # Add EOF marker to the stream
        objref_stream_client.xadd(
            self.objref,
            {"chunk": b"", "id": -1},
        )

        # Expire the stream after 20 minutes
        objref_stream_client.expire(self.objref, 1200)

        return self._asset.finalize_streaming_asset(file_bytes)

    def read(self, start_index=0, timeout=1000):
        """
        Subscribe to the stream, read the chunks and return an iterator.
        """
        message_index = start_index
        chunk = b""
        chunk_index = 0

        try:
            while True:
                stream = objref_stream_client.xread(count=10, streams={self.objref: message_index}, block=timeout)
                if not stream:
                    break

                for _, messages in stream:
                    for id, message in messages:
                        chunk_index = message[b"id"]
                        chunk = message[b"chunk"]
                        yield chunk
                        message_index = id

                if chunk_index == -1 or chunk == b"":
                    break
        except Exception as e:
            logger.error(f"Error reading stream: {e}")
            yield b""
