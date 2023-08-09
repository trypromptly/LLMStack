import logging
import pickle
from abc import ABC
from abc import abstractmethod
from typing import Generator
from typing import Generic
from typing import Optional
from typing import TypeVar

from pydantic import BaseModel
from pydantic import Field

LOGGER = logging.getLogger(__name__)


class Schema(BaseModel):
    pass


class BaseInputEnvironment(Schema):
    bypass_cache: bool = Field(True, description='Bypass cache')


class BaseError(Schema):
    code: int
    message: str


class BaseInput(Schema):
    env: Optional[BaseInputEnvironment] = Field(
        None, description='Environment variables (metadata) to be passed with input', alias='_env',
    )


class BaseConfiguration(Schema):
    pass


class BaseErrorOutput(Schema):
    error: Optional[BaseError] = Field(None, description='Error Object')


class BaseOutput(Schema):
    metadata: Optional[Schema] = Field(
        default={}, description='Metadata',
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


BaseInputType = TypeVar('BaseInputType', BaseInput, dict)
BaseOutputType = TypeVar(
    'BaseOutputType', BaseOutput,
    BaseErrorOutput, Generator[BaseOutput, None, None],
)
BaseConfigurationType = TypeVar(
    'BaseConfigurationType', BaseConfiguration, dict,
)


class BaseProcessor(Generic[BaseInputType, BaseOutputType, BaseConfigurationType], ABC):
    """
    Base class for all processors
    """

    @staticmethod
    def name() -> str:
        raise NotImplementedError

    @staticmethod
    def slug() -> str:
        return BaseProcessor.name().lower().replace(' ', '_')

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
    def get_input_schema(cls) -> dict:
        api_processor_interface_class = cls.__orig_bases__[0]
        return api_processor_interface_class.__args__[0].schema_json()

    @classmethod
    def get_output_schema(cls) -> dict:
        api_processor_interface_class = cls.__orig_bases__[0]
        return api_processor_interface_class.__args__[1].schema_json()

    @classmethod
    def get_configuration_schema(cls) -> dict:
        api_processor_interface_class = cls.__orig_bases__[0]
        return api_processor_interface_class.__args__[2].schema_json()

    def __init__(self, configuration: dict, cache_manager: CacheManager = None, input_tx_cb: callable = None, output_tx_cb: callable = None):
        self.configuration = self.parse_validate_configuration(configuration)
        self.cache_manager = cache_manager
        self._input_tx_cb = input_tx_cb
        self._output_tx_cb = output_tx_cb

    def parse_validate_input(self, input) -> BaseInputType:
        input_cls = self.__class__.__orig_bases__[0].__args__[0]
        if self._input_tx_cb:
            input = self._input_tx_cb(input)
        if type(input_cls) == type:
            return input
        return input_cls(**input)

    def parse_validate_configuration(self, configuration) -> BaseConfigurationType:
        configuration_cls = self.__class__.__orig_bases__[0].__args__[2]
        if type(configuration_cls) == type:
            return configuration
        return configuration_cls(**configuration)

    def parse_validate_output(self, **kwargs) -> BaseOutputType:
        output_cls = self.__class__.__orig_bases__[0].__args__[1]
        return output_cls(**kwargs)

    def _process(self, input: BaseInputType, configuration: BaseConfigurationType) -> BaseOutputType:
        raise NotImplementedError()

    def process(self, input: dict) -> BaseOutputType:
        try:
            return self._process(self.parse_validate_input(input), self.configuration)
        except Exception as ex:
            LOGGER.exception('Exception occurred while processing')
            raise ex

    def _process_iter(self, input: BaseInputType, configuration: BaseConfigurationType) -> BaseOutputType:
        raise NotImplementedError()

    def process_iter(self, input: dict) -> BaseOutputType:
        try:
            return self._process_iter(self.parse_validate_input(input), self.configuration)
        except Exception as ex:
            LOGGER.exception('Exception occurred while processing')
            raise ex

    def serialize(self):
        return pickle.dumps(self)

    @property
    def id(self):
        return id(self)
