import ast
import base64
import json
import logging
import uuid
from typing import Dict, List, Union

from asgiref.sync import async_to_sync

from llmstack.apps.models import App, AppData
from llmstack.apps.schemas import OutputTemplate
from llmstack.common.blocks.base.schema import BaseSchema as Schema
from llmstack.common.utils.liquid import render_template
from llmstack.play.actor import Actor
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface
from llmstack.processors.providers.promptly.promptly_app import (
    PromptlyAppConfiguration,
    PromptlyAppInput,
    PromptlyAppOutput,
    get_input_ui_schema,
    get_json_schema_from_input_fields,
    get_tool_json_schema_from_input_fields,
)

logger = logging.getLogger(__name__)


class MapProcessorInput(PromptlyAppInput):
    input_list: str = "[]"


class MapProcessorOutput(Schema):
    output_list: List[Union[str, Dict]] = []


class MapProcessorConfiguration(PromptlyAppConfiguration):
    pass


class MapProcessor(ApiProcessorInterface[MapProcessorInput, MapProcessorOutput, MapProcessorConfiguration]):
    """
    Map processor
    """

    def __init__(
        self,
        input,
        config,
        env,
        output_stream=None,
        dependencies=[],
        all_dependencies=[],
        metadata={},
        session_data=None,
        request=None,
        id=None,
        is_tool=False,
        session_enabled=True,
    ):
        Actor.__init__(
            self,
            dependencies=dependencies,
            all_dependencies=all_dependencies,
        )

        self._config = self._get_configuration_class()(**config)
        self._input = self._get_input_class()(**input)
        self._env = env
        self._id = id
        self._output_stream = output_stream
        self._is_tool = is_tool
        self._request = request
        self._metadata = metadata
        self._session_enabled = session_enabled

        self.process_session_data(session_data if session_enabled else {})

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
        return PromptlyAppInput(input=tool_args)

    @classmethod
    def get_output_template(cls) -> OutputTemplate | None:
        return OutputTemplate(markdown="{{ text }}")

    def disable_history(self) -> bool:
        return True

    @classmethod
    def api_backends(cls, context={}) -> Dict:
        api_backends = []
        request_user = context.get("request_user")
        if request_user:
            promptly_app_uuids = App.objects.filter(owner=request_user).values_list("uuid", "published_uuid")
            for app_uuid, published_app_uuid in promptly_app_uuids:
                promptly_app_data = (
                    AppData.objects.filter(app_uuid=app_uuid, is_draft=False).order_by("-version").first()
                )
                if promptly_app_data and promptly_app_data.data.get("config", {}).get("allowed_as_processor"):
                    api_backends.append(
                        {
                            "id": f"{cls.provider_slug()}/{cls.slug()}/map/{published_app_uuid}",
                            "name": f"{promptly_app_data.data.get('name')} (Map)",
                            "slug": f"{cls.slug()}/map/{published_app_uuid}",
                            "api_provider_slug": cls.provider_slug(),
                            "description": promptly_app_data.data.get("description"),
                            "input_schema": {
                                "type": "object",
                                "properties": {
                                    "input_list": {
                                        "type": "string",
                                        "title": "Input list",
                                    },
                                    "input": get_json_schema_from_input_fields(
                                        name="MapProcessorInput",
                                        input_fields=promptly_app_data.data.get("input_fields", []),
                                    ),
                                },
                            },
                            "output_schema": PromptlyAppOutput.get_schema(),
                            "config_schema": {
                                "type": "object",
                                "properties": {
                                    "app_published_uuid": {
                                        "type": "string",
                                        "title": "App Published UUID",
                                        "description": "Promptly App",
                                        "default": f"{published_app_uuid}",
                                    },
                                    "app_version": {
                                        "type": "string",
                                        "title": "App Version",
                                        "description": "App Version",
                                        "default": f"{promptly_app_data.version}",
                                    },
                                    "input_schema": {
                                        "type": "string",
                                        "title": "App Input Schema",
                                        "description": "App Input Schema",
                                        "default": f"""{json.dumps(
                                        get_tool_json_schema_from_input_fields(name='MapProcessorInput',input_fields=promptly_app_data.data.get('input_fields', [])))}""",
                                    },
                                    "objref": {
                                        "type": "boolean",
                                        "title": "Output as Object Reference",
                                        "description": "Return output as object reference instead of raw text.",
                                        "default": False,
                                    },
                                },
                                "required": ["app_published_uuid"],
                            },
                            "input_ui_schema": {
                                "input_list": {
                                    "ui:label": "Input list",
                                    "ui:description": "Input list",
                                    "ui:widget": "textarea",
                                },
                                "input": get_input_ui_schema(promptly_app_data.data.get("input_fields", [])),
                            },
                            "output_ui_schema": PromptlyAppOutput.get_ui_schema(),
                            "config_ui_schema": {
                                "app_published_uuid": {
                                    "ui:label": "App Published UUID",
                                    "ui:description": "Promptly App",
                                    "ui:advanced": False,
                                    "ui:disabled": True,
                                },
                                "app_version": {
                                    "ui:label": "App Version",
                                    "ui:description": "App Version",
                                    "ui:advanced": True,
                                },
                                "input_schema": {
                                    "ui:label": "App Input Schema",
                                    "ui:description": "App Input Schema",
                                    "ui:advanced": True,
                                    "ui:disabled": True,
                                    "ui:widget": "hidden",
                                },
                                "objref": {
                                    "ui:label": "Output as Object Reference",
                                    "ui:description": "Return output as object reference instead of raw text.",
                                    "ui:advanced": True,
                                },
                            },
                            "output_template": cls.get_output_template().dict(),
                        }
                    )

        return api_backends

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
        return buf

    def process(self) -> dict:
        from llmstack.apps.apis import AppViewSet

        _input_list = ast.literal_eval(self._input.input_list)

        logger.info(f"Processing {self.name()}")
        logger.info(f"Input: {_input_list}")

        app = App.objects.filter(published_uuid=self._config.app_published_uuid).first()
        app_data = AppData.objects.filter(app_uuid=app.uuid, version=self._config.app_version).first()
        output_template = app_data.data.get("output_template", {}).get("markdown")
        self._request.data["input"] = self._input.dict()["input"]

        response_stream, _ = AppViewSet().run_app_internal(
            str(app.uuid),
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
