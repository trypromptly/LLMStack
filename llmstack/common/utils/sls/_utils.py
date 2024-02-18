import copy
from typing import Any, Dict, Literal


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
