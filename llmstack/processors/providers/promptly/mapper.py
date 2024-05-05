import ast
import json
import logging
import uuid
from typing import List

from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.blocks.base.schema import BaseSchema as Schema
from llmstack.common.utils.liquid import render_template
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    hydrate_input,
)
from llmstack.processors.providers.promptly.promptly_app import PromptlyApp

logger = logging.getLogger(__name__)


class MapProcessorInput(Schema):
    input_list: str = Field(default="[]", description="Input list")


class MapProcessorOutput(Schema):
    outputs: List[str] = []
    objrefs: List[str] = []
    outputs_text: str = ""


class MapProcessorConfiguration(PromptlyApp):
    pass


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
        return json.loads(processor_data["config"]["input_schema"])

    def tool_invoke_input(self, tool_args: dict):
        return MapProcessorInput(input=tool_args)

    @classmethod
    def get_output_template(cls) -> OutputTemplate | None:
        markdown_template = """{% for item in output_list %}{{ item }}{% endfor %}"""
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

    async def process_response_stream_as_buffer(self, response_stream, output_template):
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

        _input_list = ast.literal_eval(self._input.input_list)

        app_data = AppData.objects.filter(
            app_uuid=self._config._promptly_app_uuid, version=self._config._promptly_app_version
        ).first()
        output_template = app_data.data.get("output_template").get("markdown")
        output_response = [""] * len(_input_list)

        for idx in range(len(_input_list)):
            item = _input_list[idx]

            hydrated_input = hydrate_input(self._config.input, {"_map_item": item})

            self._request.data["input"] = hydrated_input

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
            output_response[idx] = result

        async_to_sync(self._output_stream.write)(
            MapProcessorOutput(outputs=output_response, outputs_text=json.dumps(output_response))
        )
        output = self._output_stream.finalize()
        return output
