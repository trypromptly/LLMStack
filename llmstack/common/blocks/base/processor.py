import logging
from abc import ABC, abstractmethod
from typing import Generator, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

from llmstack.common.blocks.base.schema import BaseSchema as Schema

LOGGER = logging.getLogger(__name__)


class BaseInputEnvironment(Schema):
    pass


class BaseInput(Schema):
    env: Optional[BaseInputEnvironment] = Field(
        None,
        description="Environment variables (metadata) to be passed with input",
        alias="_env",
    )


class BaseConfiguration(Schema):
    pass


class BaseOutput(Schema):
    metadata: Optional[Schema] = Field(
        default={},
        description="Metadata",
    )


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
BaseConfigurationType = TypeVar(
    "BaseConfigurationType",
    BaseConfiguration,
    dict,
)


class ProcessorInterface(
    Generic[BaseInputType, BaseOutputType, BaseConfigurationType],
    ABC,
):
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
        return api_processor_interface_class.__args__[0].schema_json()

    @classmethod
    def _get_output_schema(cls) -> dict:
        api_processor_interface_class = cls.__orig_bases__[0]
        return api_processor_interface_class.__args__[1].schema_json()

    @classmethod
    def _get_configuration_schema(cls) -> dict:
        api_processor_interface_class = cls.__orig_bases__[0]
        return api_processor_interface_class.__args__[2].schema_json()

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


class BaseProcessor(
    ProcessorInterface[BaseInputType, BaseOutputType, BaseConfigurationType],
):
    """
    Base class for all processors
    """

    def __init__(
        self,
        configuration: dict,
        cache_manager: CacheManager = None,
        input_tx_cb: callable = None,
        output_tx_cb: callable = None,
    ):
        self.configuration = self.parse_validate_configuration(configuration)
        self.cache_manager = cache_manager
        self._input_tx_cb = input_tx_cb
        self._output_tx_cb = output_tx_cb

    def parse_validate_input(self, input) -> BaseInputType:
        input_cls = self.__class__.__orig_bases__[0].__args__[0]
        if self._input_tx_cb:
            input = self._input_tx_cb(input)
        if issubclass(input_cls, BaseModel):
            input_cls(**input)
        return input

    def parse_validate_configuration(
        self,
        configuration,
    ) -> BaseConfigurationType:
        configuration_cls = self.__class__.__orig_bases__[0].__args__[2]
        if issubclass(configuration_cls, BaseModel):
            return configuration_cls(**configuration)
        return configuration

    def parse_validate_output(self, **kwargs) -> BaseOutputType:
        output_cls = self.__class__.__orig_bases__[0].__args__[1]
        return output_cls(**kwargs)

    def _process(
        self,
        input: BaseInputType,
        configuration: BaseConfigurationType,
    ) -> BaseOutputType:
        raise NotImplementedError()

    def process(self, input: dict) -> BaseOutputType:
        try:
            return self._process(
                self.parse_validate_input(input),
                self.configuration,
            )
        except Exception as ex:
            LOGGER.exception("Exception occurred while processing")
            raise ex

    def _process_iter(
        self,
        input: BaseInputType,
        configuration: BaseConfigurationType,
    ) -> BaseOutputType:
        raise NotImplementedError()

    def process_iter(self, input: dict) -> BaseOutputType:
        try:
            return self._process_iter(
                self.parse_validate_input(input),
                self.configuration,
            )
        except Exception as ex:
            LOGGER.exception("Exception occurred while processing")
            raise ex

    @property
    def id(self):
        return id(self)
