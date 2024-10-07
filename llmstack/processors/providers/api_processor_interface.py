import logging
import time
from functools import cache
from typing import Any, Dict, Optional

import ujson as json
from django import db
from pydantic import BaseModel

from llmstack.apps.app_session_utils import get_app_session_data, save_app_session_data
from llmstack.apps.schemas import OutputTemplate
from llmstack.assets.utils import get_asset_by_objref
from llmstack.common.blocks.base.processor import (
    BaseConfigurationType,
    BaseInputType,
    BaseOutputType,
    ProcessorInterface,
)
from llmstack.common.blocks.base.schema import BaseSchema as _Schema
from llmstack.common.utils.liquid import hydrate_input
from llmstack.common.utils.provider_config import get_matched_provider_config
from llmstack.play.actor import Actor, BookKeepingData
from llmstack.play.actors.agent import ToolInvokeInput
from llmstack.play.utils import extract_jinja2_variables
from llmstack.processors.providers.config import ProviderConfig, ProviderConfigSource
from llmstack.processors.providers.metrics import MetricType

logger = logging.getLogger(__name__)


TEXT_WIDGET_NAME = "output_text"
IMAGE_WIDGET_NAME = "output_image"
AUDIO_WIDGET_NAME = "output_audio"
CHAT_WIDGET_NAME = "output_chat"
FILE_WIDGET_NAME = "file"


class ApiProcessorSchema(_Schema):
    pass


class ApiProcessorInterface(
    ProcessorInterface[BaseInputType, BaseOutputType, BaseConfigurationType],
    Actor,
):
    """
    Abstract class for API processors
    """

    def _get_session_asset(self, objref, include_data=True, include_name=True):
        from llmstack.assets.apis import AssetViewSet

        response = AssetViewSet().get_by_objref(
            self._request, objref, include_data=include_data, include_name=include_name
        )

        if response.status_code == 200:
            return response.data

        return None

    def _get_session_asset_instance(self, objref):
        return get_asset_by_objref(objref, self._request.user, self._request.session)

    # Convert objref to data URI if it exists
    def _get_session_asset_data_uri(self, objref, include_name=True):
        if not objref.startswith("objref://"):
            return objref

        asset = self._get_session_asset(objref, include_data=True, include_name=include_name)
        if asset and "data_uri" in asset:
            return asset["data_uri"]

        return objref

    def _get_all_session_assets(self, include_name=True, include_data=False, include_objref=False):
        from llmstack.assets.apis import AssetViewSet

        response = AssetViewSet().get_by_ref_id(
            self._request,
            "sessionfiles",
            self._metadata.get("session_id", ""),
            include_data=include_data,
            include_name=include_name,
            include_objref=include_objref,
        )
        if response.status_code == 200:
            return response.data

        return None

    # Upload the asset to the session
    def _upload_asset_from_url(self, asset=None, file_name=None, mime_type=None):
        from llmstack.apps.models import AppSessionFiles

        try:
            asset_metadata = {
                "app_uuid": self._metadata.get("app_uuid", ""),
                "username": self._metadata.get("username", ""),
            }

            if file_name:
                asset_metadata["file_name"] = file_name

            if mime_type:
                asset_metadata["mime_type"] = mime_type

            if not asset:
                # Defaults to streaming asset if no asset is provided
                asset = AppSessionFiles.create_streaming_asset(
                    metadata=asset_metadata, ref_id=self._metadata.get("session_id", "")
                )
            elif asset.startswith("data:"):
                asset = AppSessionFiles.create_from_data_uri(
                    asset, metadata=asset_metadata, ref_id=self._metadata.get("session_id", "")
                )
            else:
                asset = AppSessionFiles.create_from_url(
                    asset, metadata=asset_metadata, ref_id=self._metadata.get("session_id", "")
                )
        except Exception as e:
            logger.exception(e)
            db.connection.close()
            return asset

        db.connection.close()

        return asset

    def _create_asset_stream(self, mime_type, file_name=None):
        """
        Creates an asset stream that can processor can append binary data to. Once the stream is closed, the asset
        will be saved to the storage and the asset will be available for download.
        """
        from llmstack.assets.stream import AssetStream

        asset = self._upload_asset_from_url(mime_type=mime_type, file_name=file_name)

        if asset:
            return AssetStream(asset)
        return None

    def __init__(
        self,
        input,
        config,
        env,
        session_id="",
        coordinator_urn=None,
        dependencies=[],
        metadata={},
        request=None,
        id=None,
        is_tool=False,
        session_enabled=True,
    ):
        Actor.__init__(
            self,
            id=id,
            coordinator_urn=coordinator_urn,
            output_cls=self._get_output_class(),
            dependencies=dependencies,
        )

        self._config = self._get_configuration_class()(**config)
        self._input = self._get_input_class()(**input)
        self._config_template = self._get_configuration_class()(**config)
        self._input_template = self._get_input_class()(**input)
        self._env = env
        self._session_id = session_id
        self._is_tool = is_tool
        self._request = request
        self._metadata = metadata
        self._session_enabled = session_enabled
        self._usage_data = [("promptly/*/*/*", MetricType.INVOCATION, (ProviderConfigSource.PLATFORM_DEFAULT, 1))]

        session_data = get_app_session_data(self._session_id, self._id)
        if self._session_enabled:
            self.process_session_data(session_data or {})

    @classmethod
    def get_output_schema(cls) -> dict:
        schema = json.loads(cls._get_output_schema())

        if "description" in schema:
            schema.pop("description")
        if "title" in schema:
            schema.pop("title")
        if "api_response" in schema["properties"]:
            schema["properties"].pop("api_response")
        for property in schema["properties"]:
            if "title" in schema["properties"][property]:
                schema["properties"][property].pop("title")
        return json.dumps(schema)

    @classmethod
    def get_output_ui_schema(cls) -> dict:
        ui_schema = cls._get_output_ui_schema()
        schema = json.loads(cls._get_output_schema())
        for key in schema["properties"].keys():
            if "widget" in schema["properties"][key]:
                ui_schema[key] = {
                    "ui:widget": schema["properties"][key]["widget"],
                }
        ui_schema["ui:submitButtonOptions"] = {
            "norender": True,
        }

        return ui_schema

    @classmethod
    def get_tool_input_schema(cls, processor_data) -> dict:
        from llmstack.common.utils.utils import get_tool_json_schema_from_input_fields

        if processor_data and processor_data.get("input_fields", None):
            return get_tool_json_schema_from_input_fields(name="", input_fields=processor_data["input_fields"])

        return json.loads(cls.get_input_schema())

    @classmethod
    def get_output_template(cls) -> Optional[OutputTemplate]:
        # Default output_template to use in tools and playground
        return None

    @classmethod
    def get_parent_processor_slug(cls):
        return None

    @classmethod
    def api_backends(cls, context={}) -> Dict:
        return [
            {
                "id": f"{cls.provider_slug()}/{cls.slug()}",  # Unique ID for the processor
                "name": cls.name(),  # Name of the processor
                "slug": cls.slug(),  # Slug of the processor
                "description": cls.description(),  # Description of the processor
                "provider_slug": cls.provider_slug(),
                "input_schema": json.loads(cls.get_input_schema()),  # Input schema of the processor
                "output_schema": json.loads(cls.get_output_schema()),  # Output schema of the processor
                "config_schema": json.loads(cls.get_configuration_schema()),  # Configuration schema of the processor
                "input_ui_schema": cls.get_input_ui_schema(),  # Input UI schema of the processor
                "output_ui_schema": cls.get_output_ui_schema(),  # Output UI schema of the processor
                "config_ui_schema": cls.get_configuration_ui_schema(),  # Configuration UI schema of the processor
                "output_template": (
                    cls.get_output_template().model_dump() if cls.get_output_template() else None
                ),  # Output template of the processor
            }
        ]

    @cache
    def get_provider_config(
        self, model_slug: str = "*", deployment_key: str = "*", provider_slug=None, processor_slug=None
    ) -> ProviderConfig:
        """
        Finds the provider config schema class and get the
        """
        return get_matched_provider_config(
            provider_configs=self._env.get("provider_configs", {}),
            provider_slug=provider_slug or self.provider_slug(),
            processor_slug=processor_slug or self.slug(),
            model_slug=model_slug,
            deployment_key=deployment_key,
        )

    def disable_history(self) -> bool:
        return False

    def process(self) -> dict:
        raise NotImplementedError

    # Used to persist data to app session
    def session_data_to_persist(self) -> dict:
        return {}

    # Used to track usage data
    def usage_data(self) -> dict:
        return {"credits": 1000, "usage_metrics": self._usage_data}

    def is_output_cacheable(self) -> bool:
        return True

    def validate(self, input: dict):
        """
        Validate the input
        """
        pass

    def process_session_data(self, session_data: dict):
        """
        Process session data
        """
        pass

    def validate_and_process(self) -> str:
        """
        Validate and process the input
        """
        processed_input = {}
        # TODO: hydrate the input with template values
        processed_input = input

        # Do other validations if any
        self.validate(processed_input)

        # Process the input
        result = self.process(processed_input)
        if isinstance(result, dict):
            return result
        elif isinstance(result, ApiProcessorSchema):
            return result.model_dump()
        else:
            logger.exception("Invalid result type")
            raise Exception("Invalid result type")

    def get_bookkeeping_data(self) -> BookKeepingData:
        None

    def get_dependencies(self):
        # Iterate over string templates in values of input and config and
        # extract dependencies
        dependencies = []
        dependencies.extend(extract_jinja2_variables(self._input))
        dependencies.extend(extract_jinja2_variables(self._config))

        # In case of _inputs0.xyz, extract _inputs0 as dependency
        dependencies = [x.split(".")[0] for x in dependencies]
        return list(set(dependencies))

    def input(self, message: Any) -> Any:
        # Hydrate the input and config before processing
        if self._is_tool:
            # NO-OP when the processor is a tool
            return
        try:
            self._input = (
                hydrate_input(
                    self._input_template,
                    message,
                )
                if message
                else self._input_template
            )
            self._config = (
                hydrate_input(
                    self._config_template,
                    message,
                )
                if self._config and message
                else self._config_template
            )
            output = self.process()
        except Exception as e:
            logger.exception("Error processing input")
            output = {
                "errors": [str(e)],
                "raw_response": {
                    "text": str(e),
                    "status_code": 400,
                },
            }

            # Send error to output stream
            self._output_stream.error(e)

        bookkeeping_data = self.get_bookkeeping_data()
        input_dict = self._input.model_dump() if self._input and isinstance(self._input, BaseModel) else self._input
        config_dict = (
            self._config.model_dump() if self._config and isinstance(self._config, BaseModel) else self._config
        )
        output_dict = {}
        if output:
            output_dict = output.model_dump() if isinstance(output, BaseModel) else output

        if not bookkeeping_data:
            bookkeeping_data = BookKeepingData(
                input=input_dict,
                config=config_dict,
                output=output_dict,
                session_data=self.session_data_to_persist() if self._session_enabled else {},
                timestamp=time.time(),
                disable_history=self.disable_history(),
            )
        if bookkeeping_data:
            bookkeeping_data.usage_data = self.usage_data()

            # Persist session_data
            save_app_session_data(self._session_id, self._id, bookkeeping_data.session_data)

        self._output_stream.bookkeep(bookkeeping_data)

    def tool_invoke_input(self, tool_args: dict) -> ToolInvokeInput:
        return self._get_input_class()(
            **{**self._input.model_dump(), **tool_args},
        )

    def invoke(self, message: ToolInvokeInput) -> Any:
        try:
            self._input = (
                hydrate_input(
                    self._input_template,
                    {**message.input, **message.tool_args},
                )
                if message
                else self._input_template
            )
            self._config = (
                hydrate_input(
                    self._config_template,
                    {**message.input, **message.tool_args},
                )
                if self._config_template
                else self._config_template
            )

            # Merge tool args with input
            self._input = self.tool_invoke_input(message.tool_args)

            logger.info(
                f"Invoking tool {message.tool_name} with args {message.tool_args}",
            )
            output = self.process()
        except Exception as e:
            logger.exception("Error invoking tool")
            output = {
                "errors": [str(e)],
                "raw_response": {
                    "text": str(e),
                    "status_code": 400,
                },
            }

            # Send error to output stream
            self._output_stream.error(e)

        bookkeeping_data = self.get_bookkeeping_data()
        if not bookkeeping_data:
            bookkeeping_data = BookKeepingData(
                input=self._input,
                config=self._config,
                output=output or {},
                session_data=self.session_data_to_persist() if self._session_enabled else {},
                timestamp=time.time(),
                disable_history=self.disable_history(),
            )

        if bookkeeping_data:
            bookkeeping_data.usage_data = self.usage_data()

        self._output_stream.bookkeep(bookkeeping_data)

    def input_stream(self, message: Any) -> Any:
        # We do not support input stream for this processor
        pass
