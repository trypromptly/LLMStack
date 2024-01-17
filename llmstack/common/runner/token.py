import json
import logging
import re
import sys

import redis

logger = logging.getLogger(__name__)


class TokenRedis:
    def __init__(self, src):
        try:
            # Split parts and use defaults for missing fields
            parts = src.split(":")
            self._server = parts[0]
            self._port = int(parts[1]) if len(parts) > 1 and parts[1] else 6379
            self._db = int(parts[2]) if len(parts) > 2 and parts[2] else 0
            self._password = parts[3] if len(parts) > 3 else None

            logger.info(
                f"TokenRedis initialized ({self._server}:{self._port})",
            )
        except (ValueError, IndexError):
            logger.error(f"Invalid format: {src}")
            sys.exit()

    def lookup(self, token):
        logger.info(f'resolving token "{token}"')
        client = redis.Redis(
            host=self._server,
            port=self._port,
            db=self._db,
            password=self._password,
        )

        stuff = client.get(token)
        if stuff is None:
            return None

        response_str = stuff.decode("utf-8").strip()
        logger.debug(f"response from redis: {response_str}")

        try:
            # Attempt to load JSON
            if response_str.startswith("{"):
                data = json.loads(response_str)
                host, port = data["host"].split(":")
            # Or parse simple format
            elif re.match(r"\S+:\S+", response_str):
                host, port = response_str.split(":")
            else:
                raise ValueError("Unable to parse token")
            return [host, port]
        except (ValueError, json.JSONDecodeError):
            logger.error(f"Unable to process token: {response_str}")
            return None
