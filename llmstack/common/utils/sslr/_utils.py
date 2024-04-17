import copy
import json as jsonlib
from typing import Any, Dict, Literal

from openai._compat import cached_property  # type: ignore # noqa: F401
from openai._utils import (  # type: ignore # noqa: F401
    deepcopy_minimal,
    extract_files,
    is_mapping,
    maybe_transform,
    required_args,
)


def generate_uuid(_str: str = None):
    import hashlib
    import uuid

    if _str:
        input_hash = hashlib.sha256(b"your_data_here").hexdigest()
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, input_hash))

    return str(uuid.uuid4())


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


def convert_google_function_call_args_map_to_dict(args):
    result = {}
    for i in args:
        result[str(i)] = str(args[i])
    return result


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


def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    import tiktoken

    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


# Logic copied from OpenAI cookbook
def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613"):
    import tiktoken

    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if model in {
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
    }:
        tokens_per_message = 3
        tokens_per_name = 1
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif "gpt-3.5-turbo" in model:
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")
    elif "gpt-4" in model:
        return num_tokens_from_messages(messages, model="gpt-4-0613")
    # Approximation for Googles gemini models
    elif "gemini-pro" in model:
        return int(num_tokens_from_messages(messages, model="gpt-4-0613") * 1.15)
    else:
        return num_tokens_from_messages(messages, model="gpt-4-0613")
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            value = value or ""
            # Temp hack for tool calls
            value = str(value)
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens
