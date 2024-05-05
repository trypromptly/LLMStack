import ast
import logging
import re
import uuid
from functools import reduce
from typing import Any, Optional

from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.common.blocks.base.schema import BaseSchema as Schema
from llmstack.common.utils.liquid import render_template
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    hydrate_input,
)
from llmstack.processors.providers.promptly.promptly_app import PromptlyApp

logger = logging.getLogger(__name__)

reducer_template_acc_var_regex = re.compile(r"\{\{\s*?_reduce_acc\s*?\s*?\}\}")
reducer_template_item_var_regex = re.compile(r"\{\{\s*?_reduce_item\s*?\s*?\}\}")


class ReduceProcessorInput(Schema):
    input_list: str = Field(default="[]", description="Input list")


class ReduceProcessorOutput(Schema):
    output: str
    objref: Optional[str] = None


class ReduceProcessorConfiguration(PromptlyApp):
    objref: Optional[bool] = Field(
        default=False,
        title="Output as Object Reference",
        description="Return output as object reference instead of raw text.",
        advanced_parameter=True,
    )


class ReduceProcessor(
    ApiProcessorInterface[ReduceProcessorInput, ReduceProcessorOutput, ReduceProcessorConfiguration],
):
    """
    Reduce processor
    """

    @staticmethod
    def name() -> str:
        return "Reduce"

    @staticmethod
    def slug() -> str:
        return "reduce"

    @staticmethod
    def description() -> str:
        return "Applies a reducer function to reduce the input list to a single result"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    async def process_response_stream(self, response_stream, output_template):
        buf = ""
        async for resp in response_stream:
            if resp.get("session") and resp.get("csp") and resp.get("template"):
                self._store_run_session_id = resp["session"]
                continue
            rendered_output = render_template(output_template, resp)
            buf += rendered_output
        return buf

    def input(self, message: Any) -> Any:
        self._reducer_dict = {}
        config_input = self._config.input

        for key, value in config_input.items():
            if isinstance(value, str) and (
                reducer_template_acc_var_regex.match(value) or reducer_template_item_var_regex.match(value)
            ):
                self._reducer_dict[key] = value
        return super().input(message)

    def process(self) -> dict:
        from llmstack.apps.apis import AppViewSet
        from llmstack.apps.models import AppData

        _input_list = ast.literal_eval(self._input.input_list)

        app_data = AppData.objects.filter(
            app_uuid=self._config._promptly_app_uuid, version=self._config._promptly_app_version
        ).first()
        output_template = app_data.data.get("output_template").get("markdown")

        def reduce_fn(acc, item):
            app_input = {**self._config.input, **self._reducer_dict}
            hydrated_input = hydrate_input(app_input, {"_reduce_acc": acc, "_reduce_item": item})
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
            return result

        reduced_result = reduce(reduce_fn, _input_list)
        async_to_sync(self._output_stream.write)(ReduceProcessorOutput(output=reduced_result))
        output = self._output_stream.finalize()
        return output
