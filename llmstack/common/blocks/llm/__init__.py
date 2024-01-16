import logging

from llmstack.common.blocks.base.processor import (BaseConfigurationType,
                                                   BaseInputType,
                                                   BaseOutputType,
                                                   CacheManager,
                                                   ProcessorInterface)

LOGGER = logging.getLogger(__name__)


class LLMBaseProcessor(
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
        if isinstance(input_cls, type):
            return input
        return input_cls(**input)

    def parse_validate_configuration(
        self,
        configuration,
    ) -> BaseConfigurationType:
        configuration_cls = self.__class__.__orig_bases__[0].__args__[2]
        if isinstance(configuration_cls, type):
            return configuration
        return configuration_cls(**configuration)

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
