import copy
import json as jsonlib
from typing import Any, Dict, Literal

from openai._utils import is_mapping  # type: ignore # noqa: F401


class LLMHttpResponse:
    def __init__(self, response, json):
        self._response = response
        self.elapsed = response.elapsed
        self.request = response.request
        self.http_version = response.http_version
        self.reason_phrase = response.reason_phrase
        self.url = response.url

        self.text = jsonlib.dumps(json)
        self.content = self.text.encode(response.encoding)
        self._json = json

        self.encoding = response.encoding
        self.charset_encoding = response.charset_encoding
        self.is_informational = response.is_informational
        self.is_success = response.is_success
        self.is_redirect = response.is_redirect
        self.is_client_error = response.is_client_error
        self.is_server_error = response.is_server_error
        self.is_error = response.is_error
        self.has_redirect_location = response.has_redirect_location
        self.raise_for_status = response.raise_for_status
        self.cookies = response.cookies
        self.links = response.links
        self.num_bytes_downloaded = response.num_bytes_downloaded
        self.headers = response.headers

    def __repr__(self):
        return f"<LLMResponse [{self.response.status_code}]>"

    def json(self):
        return self._json

    def read(self):
        return self.content


def _convert_schema_dict_to_gapic(schema_dict: Dict[str, Any]):
    """Converts a JsonSchema to a dict that the GAPIC Schema class accepts."""
    gapic_schema_dict = copy.copy(schema_dict)
    if "type" in gapic_schema_dict:
        gapic_schema_dict["type_"] = gapic_schema_dict.pop("type").upper()
    if "format" in gapic_schema_dict:
        gapic_schema_dict["format_"] = gapic_schema_dict.pop("format")
    if "items" in gapic_schema_dict:
        gapic_schema_dict["items"] = _convert_schema_dict_to_gapic(
            gapic_schema_dict["items"],
        )
    properties = gapic_schema_dict.get("properties")
    if properties:
        for property_name, property_schema in properties.items():
            properties[property_name] = _convert_schema_dict_to_gapic(
                property_schema,
            )
    return gapic_schema_dict


def google_finish_reason_to_literal(
    finish_reason: str,
) -> Literal["stop", "length", "tool_calls", "content_filter", "function_call"]:
    from google.ai.generativelanguage_v1beta.types.generative_service import Candidate

    if finish_reason == Candidate.FinishReason.STOP:
        return "stop"
    elif finish_reason == Candidate.FinishReason.MAX_TOKENS:
        return "length"

    return "stop"
