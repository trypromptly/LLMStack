import base64
import json
import logging
import uuid
from typing import Dict, List, Optional

from asgiref.sync import async_to_sync
from pydantic import Field, PrivateAttr, model_validator

from llmstack.apps.schemas import OutputTemplate
from llmstack.apps.yaml_loader import get_input_model_from_fields
from llmstack.common.blocks.base.schema import BaseSchema as Schema
from llmstack.common.blocks.base.schema import CustomGenerateJsonSchema
from llmstack.common.utils.liquid import render_template
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface

logger = logging.getLogger(__name__)


def get_json_schema_from_input_fields(name="", input_fields=[]):
    return get_input_model_from_fields(name=name, input_fields=input_fields).model_json_schema(
        schema_generator=CustomGenerateJsonSchema
    )


def get_tool_json_schema_from_input_fields(name="", input_fields=[]):
    input_schema = get_input_model_from_fields(name=name, input_fields=input_fields).model_json_schema(
        schema_generator=CustomGenerateJsonSchema
    )
    tool_schema = {"type": "object", "properties": {}}

    for key, value in input_schema["properties"].items():
        tool_schema["properties"][key] = {
            "type": value["type"],
            "description": value.get("description", ""),
        }

    return tool_schema


def get_input_ui_schema(input_fields=[]):
    ui_schema = {}
    for field in input_fields:
        ui_schema[field["name"]] = {}
        if field["type"] == "text":
            ui_schema[field["name"]]["ui:widget"] = "textarea"
        if field["type"] == "boolean":
            ui_schema[field["name"]]["ui:widget"] = "radio"

        if field["type"] in ["text", "voice", "file", "datasource", "connection", "select", "multi"]:
            ui_schema[field["name"]]["ui:widget"] = "text"

        if field["type"] == "select":
            ui_schema[field["name"]]["ui:widget"] = "select"
            if field.get("ui:options"):
                ui_schema[field["name"]]["ui:options"] = field["ui:options"]

    return ui_schema


class PromptlyApp(Schema):
    promptly_app: str = Field(
        default="{}",
        description="Promptly App Configuration",
        json_schema_extra={"advanced_parameter": False, "widget": "promptlyapp_select"},
    )
    _input: Dict = PrivateAttr(default={})
    _promptly_app_uuid: str = PrivateAttr(default="")
    _promptly_app_published_uuid: str = PrivateAttr(default="")
    _promptly_app_version: str = PrivateAttr(default="")
    _promptl_app_input_fields: List[Dict] = PrivateAttr(default=[])
    _proptly_app: Dict = PrivateAttr(default={})
    _input_schema: Dict = PrivateAttr(default={})
    _tool_schema: Dict = PrivateAttr(default={})

    @model_validator(mode="before")
    def validate_input(cls, values):
        promptly_app = values.get("promptly_app", "{}")
        promptly_app_json = json.loads(promptly_app)

        values["_promptly_app_uuid"] = promptly_app_json.get("promptly_app_uuid", "")
        values["_promptly_app_published_uuid"] = promptly_app_json.get("promptly_app_published_uuid", "")
        values["_promptly_app_version"] = promptly_app_json.get("promptly_app_version", "")
        values["_promptly_app_input_fields"] = promptly_app_json.get("promptly_app_input_fields", [])
        values["_promptly_output_template"] = promptly_app_json.get("promptly_output_template", {})
        values["_input_schema"] = get_json_schema_from_input_fields(
            name="PromptlyAppInput", input_fields=values["_promptly_app_input_fields"]
        )
        values["_tool_schema"] = get_tool_json_schema_from_input_fields(
            name="PromptlyAppInput", input_fields=values["_promptly_app_input_fields"]
        )
        values["_input"] = promptly_app_json.get("input", {})
        return values


class PromptlyAppInput(Schema):
    input: Dict = Field(default={}, description="Input", json_schema_extra={"widget": "hidden"})


class PromptlyAppOutput(Schema):
    text: str = Field(default="", description="Promptly App Output as Text")
    objref: Optional[str] = Field(default=None, description="Promptly App Output as Object Reference")
    processing: Optional[bool] = Field(default=None, description="processing", json_schema_extra={"widget": "hidden"})


class PromptlyAppConfiguration(PromptlyApp):
    objref: Optional[bool] = Field(
        default=False,
        title="Output as Object Reference",
        description="Return output as object reference instead of raw text.",
    )


class PromptlyAppProcessor(ApiProcessorInterface[PromptlyAppInput, PromptlyAppOutput, PromptlyAppConfiguration]):
    @staticmethod
    def name() -> str:
        return "Promptly App"

    @staticmethod
    def slug() -> str:
        return "promptly_app"

    @staticmethod
    def description() -> str:
        return "Use your promptly app as a processor"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    @classmethod
    def get_tool_input_schema(cls, processor_data) -> dict:
        promptly_app_input_fields = json.loads(processor_data["config"]["promptly_app"])["promptly_app_input_fields"]
        tool_input_schema = get_tool_json_schema_from_input_fields("PromptlyAppInput", promptly_app_input_fields)
        return tool_input_schema

    def tool_invoke_input(self, tool_args: dict):
        return PromptlyAppInput(input=tool_args, input_json=json.dumps(tool_args))

    @classmethod
    def get_output_template(cls) -> OutputTemplate | None:
        return OutputTemplate(markdown="{{ text }}", jsonpath="$.text")

    def disable_history(self) -> bool:
        return True

    async def process_response_stream(self, response_stream, output_template):
        async for resp in response_stream:
            if resp.get("session") and resp.get("csp") and resp.get("template"):
                self._store_run_session_id = resp["session"]
                continue
            rendered_output = render_template(output_template, resp)
            await self._output_stream.write(PromptlyAppOutput(text=rendered_output))

    async def process_response_stream_as_buffer(self, response_stream, output_template):
        buf = ""
        async for resp in response_stream:
            if resp.get("session") and resp.get("csp") and resp.get("template"):
                self._store_run_session_id = resp["session"]
                continue
            rendered_output = render_template(output_template, resp)
            buf += rendered_output
            async_to_sync(self._output_stream.write)(PromptlyAppOutput(processing=True))
        return buf

    def process(self) -> dict:
        from llmstack.apps.apis import AppViewSet
        from llmstack.apps.models import AppData

        promptly_app = json.loads(self._config.promptly_app)
        app_data = AppData.objects.filter(
            app_uuid=promptly_app["promptly_app_uuid"], version=promptly_app["promptly_app_version"]
        ).first()
        output_template = app_data.data.get("output_template").get("markdown")

        self._request.data["input"] = {**promptly_app["input"], **self._input.input}
        logger.info(f"Promptly App Input: {self._request.data}")
        response_stream, _ = AppViewSet().run_app_internal(
            promptly_app["promptly_app_uuid"],
            self._metadata.get("session_id"),
            str(uuid.uuid4()),
            self._request,
            platform="promptly",
            preview=False,
            app_store_uuid=None,
        )

        if self._config.objref:
            result_text = async_to_sync(self.process_response_stream_as_buffer)(
                response_stream, output_template=output_template
            )
            file_name = str(uuid.uuid4()) + ".txt"
            data_uri = f"data:text/plain;name={file_name};base64,{base64.b64encode(result_text.encode('utf-8')).decode('utf-8')}"
            asset = self._upload_asset_from_url(asset=data_uri)
            async_to_sync(self._output_stream.write)(PromptlyAppOutput(objref=asset))
        else:
            async_to_sync(self.process_response_stream)(response_stream, output_template=output_template)

        output = self._output_stream.finalize()
        return output
