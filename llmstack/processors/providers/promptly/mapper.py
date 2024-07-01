import ast
import base64
import json
import logging
import uuid
from typing import Dict, List, Optional

from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.blocks.base.schema import BaseSchema as Schema
from llmstack.common.utils.liquid import render_template
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface
from llmstack.processors.providers.promptly.promptly_app import (
    PromptlyApp,
    get_tool_json_schema_from_input_fields,
)

logger = logging.getLogger(__name__)


class MapProcessorInput(Schema):
    input_list: List[Dict] = Field(default=[], description="Input list", json_schema_extra={"widget": "hidden"})
    input_list_json: str = Field(default="[]", description="Input list", json_schema_extra={"widget": "hidden"})


class MapProcessorOutput(Schema):
    outputs: List[str] = []
    objrefs: List[str] = []
    outputs_text: str = ""
    processing: Optional[bool] = Field(default=None, description="processing", json_schema_extra={"widget": "hidden"})


class MapProcessorConfiguration(PromptlyApp):
    objref: Optional[bool] = Field(
        default=False,
        title="Output as Object Reference",
        description="Return output as object reference instead of raw text.",
    )


class MapProcessor(ApiProcessorInterface[MapProcessorInput, MapProcessorOutput, MapProcessorConfiguration]):
    """
    Map processor
    """

    @staticmethod
    def name() -> str:
        return "Map"

    @staticmethod
    def slug() -> str:
        return "map"

    @staticmethod
    def description() -> str:
        return "Applies a mapper function to each item in the input list"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    @classmethod
    def get_tool_input_schema(cls, processor_data) -> dict:
        promptly_app_input_fields = json.loads(processor_data["config"]["promptly_app"])["promptly_app_input_fields"]
        promptly_app_tool_schema = get_tool_json_schema_from_input_fields("PromptlyAppInput", promptly_app_input_fields)
        tool_input_schema = {"type": "object", "properties": {}}
        tool_input_schema["properties"]["input_list"] = {
            "type": "array",
            "items": promptly_app_tool_schema,
            "description": "A list of input messages",
        }
        return tool_input_schema

    def tool_invoke_input(self, tool_args: dict):
        return MapProcessorInput(input_list=tool_args["input_list"])

    @classmethod
    def get_output_template(cls) -> OutputTemplate | None:
        markdown_template = """{{outputs_text}}"""
        return OutputTemplate(markdown=markdown_template)

    def disable_history(self) -> bool:
        return True

    async def process_response_stream(self, response_stream, output_template):
        buf = ""
        async for resp in response_stream:
            if resp.get("session") and resp.get("csp") and resp.get("template"):
                self._store_run_session_id = resp["session"]
                continue
            rendered_output = render_template(output_template, resp)
            buf += rendered_output
        return buf

    def process(self) -> dict:
        from llmstack.apps.apis import AppViewSet
        from llmstack.apps.models import AppData

        if self._input.input_list_json and not self._input.input_list:
            try:
                self._input.input_list = json.loads(self._input.input_list_json)
            except json.JSONDecodeError:
                self._input.input_list = ast.literal_eval(self._input.input_list_json)

        _input_list = self._input.input_list

        app_data = AppData.objects.filter(
            app_uuid=self._config._promptly_app_uuid, version=self._config._promptly_app_version
        ).first()
        output_template = app_data.data.get("output_template").get("markdown")
        output_response = [""] * len(_input_list)

        for idx in range(len(_input_list)):
            app_input = {**self._config.input, **_input_list[idx]}
            self._request.data["input"] = app_input

            response_stream, _ = AppViewSet().run_app_internal(
                self._config._promptly_app_uuid,
                self._metadata.get("session_id"),
                str(uuid.uuid4()),
                self._request,
                platform="promptly",
                preview=False,
                app_store_uuid=None,
            )

            result = async_to_sync(self.process_response_stream)(response_stream, output_template=output_template)
            async_to_sync(self._output_stream.write)(MapProcessorOutput(processing=True))
            output_response[idx] = result

        if self._config.objref:
            objrefs = []
            for result_text in output_response:
                file_name = str(uuid.uuid4()) + ".txt"
                data_uri = f"data:text/plain;name={file_name};base64,{base64.b64encode(result_text.encode('utf-8')).decode('utf-8')}"
                objrefs.append(self._upload_asset_from_url(asset=data_uri))
            async_to_sync(self._output_stream.write)(
                MapProcessorOutput(objrefs=objrefs, outputs_text=json.dumps(output_response))
            )
        else:
            async_to_sync(self._output_stream.write)(
                MapProcessorOutput(outputs=output_response, outputs_text=json.dumps(output_response))
            )
        output = self._output_stream.finalize()
        return output
