import json
import logging
from abc import ABC, abstractmethod
from typing import Generator, Generic, TypeVar

from llmstack.common.blocks.base.schema import BaseSchema as Schema
from llmstack.common.blocks.base.schema import CustomGenerateJsonSchema

LOGGER = logging.getLogger(__name__)


class BaseInput(Schema):
    pass


class BaseConfiguration(Schema):
    pass


class BaseOutput(Schema):
    pass


class CacheManager(ABC):
    @abstractmethod
    def set(self, key, value):
        raise NotImplementedError()

    @abstractmethod
    def get(self, key):
        raise NotImplementedError()

    @abstractmethod
    def delete(self, key):
        raise NotImplementedError()


BaseInputType = TypeVar("BaseInputType", BaseInput, dict)
BaseOutputType = TypeVar("BaseOutputType", BaseOutput, dict)
BaseConfigurationType = TypeVar("BaseConfigurationType", BaseConfiguration, dict)


class ProcessorInterface(Generic[BaseInputType, BaseOutputType, BaseConfigurationType], ABC):
    @staticmethod
    def name() -> str:
        raise NotImplementedError

    @staticmethod
    def slug() -> str:
        raise NotImplementedError

    @staticmethod
    def description() -> str:
        raise NotImplementedError

    @staticmethod
    def provider_slug() -> str:
        raise NotImplementedError

    @staticmethod
    def tool_only() -> bool:
        """
        Should be used exclusively as a tool
        """
        return False

    @classmethod
    def _get_input_class(cls) -> BaseInputType:
        return cls.__orig_bases__[0].__args__[0]

    @classmethod
    def _get_output_class(cls) -> BaseOutputType:
        return cls.__orig_bases__[0].__args__[1]

    @classmethod
    def _get_configuration_class(cls) -> BaseConfigurationType:
        return cls.__orig_bases__[0].__args__[2]

    @classmethod
    def _get_input_schema(cls) -> dict:
        api_processor_interface_class = cls.__orig_bases__[0]
        return json.dumps(
            api_processor_interface_class.__args__[0].model_json_schema(schema_generator=CustomGenerateJsonSchema)
        )

    @classmethod
    def _get_output_schema(cls) -> dict:
        api_processor_interface_class = cls.__orig_bases__[0]
        return json.dumps(
            api_processor_interface_class.__args__[1].model_json_schema(schema_generator=CustomGenerateJsonSchema)
        )

    @classmethod
    def _get_configuration_schema(cls) -> dict:
        api_processor_interface_class = cls.__orig_bases__[0]
        return json.dumps(
            api_processor_interface_class.__args__[2].model_json_schema(schema_generator=CustomGenerateJsonSchema)
        )

    @classmethod
    def _get_input_ui_schema(cls) -> dict:
        api_processor_interface_class = cls.__orig_bases__[0]
        return api_processor_interface_class.__args__[0].get_ui_schema()

    @classmethod
    def _get_output_ui_schema(cls) -> dict:
        api_processor_interface_class = cls.__orig_bases__[0]
        return api_processor_interface_class.__args__[1].get_ui_schema()

    @classmethod
    def _get_configuration_ui_schema(cls) -> dict:
        api_processor_interface_class = cls.__orig_bases__[0]
        return api_processor_interface_class.__args__[2].get_ui_schema()

    @classmethod
    def get_input_cls(cls) -> BaseInputType:
        return cls._get_input_class()

    @classmethod
    def get_output_cls(cls) -> BaseOutputType:
        return cls._get_output_class()

    @classmethod
    def get_configuration_cls(cls) -> BaseConfigurationType:
        return cls._get_configuration_class()

    @classmethod
    def get_input_schema(cls) -> dict:
        return cls._get_input_schema()

    @classmethod
    def get_output_schema(cls) -> dict:
        return cls._get_output_schema()

    @classmethod
    def get_configuration_schema(cls) -> dict:
        return cls._get_configuration_schema()

    @classmethod
    def get_input_ui_schema(cls) -> dict:
        return cls._get_input_ui_schema()

    @classmethod
    def get_output_ui_schema(cls) -> dict:
        return cls._get_output_ui_schema()

    @classmethod
    def get_configuration_ui_schema(cls) -> dict:
        return cls._get_configuration_ui_schema()

    def process(
        self,
        input: BaseInputType,
        configuration: BaseConfigurationType,
    ) -> BaseOutputType:
        raise NotImplementedError()

    def process_iter(
        self,
        input: BaseInputType,
        configuration: BaseConfigurationType,
    ) -> Generator[BaseOutputType, None, None]:
        raise NotImplementedError()
