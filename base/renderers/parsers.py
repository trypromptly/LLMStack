from typing import Any
from typing import Mapping
from typing import Optional
from typing import Type

import orjson
import ujson
from django.conf import settings
from rest_framework.exceptions import ParseError
from rest_framework.parsers import BaseParser
from rest_framework.renderers import BaseRenderer
from rest_framework.renderers import JSONRenderer

__all__ = ['UJSONParser', 'ORJSONParser']


class UJSONParser(BaseParser):
    """
    Parses JSON-serialized data by ujson parser.
    """

    media_type: str = 'application/json'
    renderer_class: Type[BaseRenderer] = JSONRenderer

    def parse(
        self,
        stream,
        media_type: Optional[str] = None,
        parser_context: Optional[Mapping[str, Any]] = None,
    ) -> dict:
        """
        Parses the incoming bytestream as JSON and returns the resulting data.
        """
        parser_context = parser_context or {}
        encoding = parser_context.get('encoding', settings.DEFAULT_CHARSET)

        try:
            data = stream.read().decode(encoding)
            return ujson.loads(data)
        except ValueError as exc:
            raise ParseError('JSON parse error - %s' % str(exc))


class ORJSONParser(BaseParser):
    """
    Parses JSON-serialized data by orjson parser.
    """

    media_type: str = 'application/json'
    renderer_class: Type[BaseRenderer] = JSONRenderer

    def parse(
        self,
        stream,
        media_type: Optional[str] = None,
        parser_context: Optional[Mapping[str, Any]] = None,
    ) -> dict:
        """
        Parses the incoming bytestream as JSON and returns the resulting data.
        """
        parser_context = parser_context or {}
        encoding = parser_context.get('encoding', settings.DEFAULT_CHARSET)

        try:
            data = stream.read().decode(encoding)
            return orjson.loads(data)
        except ValueError as exc:
            raise ParseError('JSON parse error - %s' % str(exc))
