import logging
import time
from typing import Any
from typing import TypeVar

import ujson as json
from pydantic import AnyUrl

from llmstack.common.blocks.base.schema import BaseSchema as _Schema
from llmstack.common.blocks.base.processor import BaseInputType, BaseOutputType, BaseConfigurationType, ProcessorInterface
from llmstack.common.utils.utils import hydrate_input
from llmstack.play.actor import Actor, BookKeepingData
from llmstack.play.utils import extract_jinja2_variables


LOGGER = logging.getLogger(__name__)

ConfigurationSchemaType = TypeVar('ConfigurationSchemaType')
InputSchemaType = TypeVar('InputSchemaType')
OutputSchemaType = TypeVar('OutputSchemaType')

TEXT_WIDGET_NAME = 'output_text'
IMAGE_WIDGET_NAME = 'output_image'
AUDIO_WIDGET_NAME = 'output_audio'
CHAT_WIDGET_NAME = 'output_chat'
FILE_WIDGET_NAME = 'file'


class DataUrl(AnyUrl):
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(
            {
                'format': 'data-url',
                'pattern': r'data:(.*);name=(.*);base64,(.*)',
            },
        )


class ApiProcessorSchema(_Schema):
    pass


class ApiProcessorInterface(ProcessorInterface[BaseInputType, BaseOutputType, BaseConfigurationType], Actor):
    """
    Abstract class for API processors
    """

    def __init__(self, input, config, env, output_stream=None, dependencies=[], all_dependencies=[], session_data=None):
        Actor.__init__(self, dependencies=dependencies,
                       all_dependencies=all_dependencies)

        # TODO: This is for backward compatibility. Remove this once all the processors are updated
        if 'datasource' in config and isinstance(config['datasource'], str):
            config['datasource'] = [config['datasource']]
        if 'datasources' in config and isinstance(config['datasources'], str):
            config['datasources'] = [config['datasources']]

        self._config = self._get_configuration_class()(**config)
        self._input = self._get_input_class()(**input)
        self._env = env
        self._output_stream = output_stream

        self.process_session_data(session_data)

    @classmethod
    def get_output_schema(cls) -> dict:
        schema = json.loads(cls._get_output_schema())

        if 'description' in schema:
            schema.pop('description')
        if 'title' in schema:
            schema.pop('title')
        if 'api_response' in schema['properties']:
            schema['properties'].pop('api_response')
        for property in schema['properties']:
            if 'title' in schema['properties'][property]:
                schema['properties'][property].pop('title')
        return json.dumps(schema)

    @classmethod
    def get_output_ui_schema(cls) -> dict:
        ui_schema = cls._get_output_ui_schema()
        schema = json.loads(cls._get_output_schema())
        for key in schema['properties'].keys():
            if 'widget' in schema['properties'][key]:
                ui_schema[key] = {
                    'ui:widget': schema['properties'][key]['widget'],
                }
        ui_schema['ui:submitButtonOptions'] = {
            'norender': True,
        }

        return ui_schema

    def process(self) -> dict:
        raise NotImplementedError

    # Used to persist data to app session
    def session_data_to_persist(self) -> dict:
        return {}

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
            return result.dict()
        else:
            LOGGER.exception('Invalid result type')
            raise Exception('Invalid result type')

    def get_bookkeeping_data(self) -> BookKeepingData:
        None

    def get_dependencies(self):
        # Iterate over string templates in values of input and config and extract dependencies
        dependencies = []
        dependencies.extend(extract_jinja2_variables(self._input))
        dependencies.extend(extract_jinja2_variables(self._config))

        # In case of _inputs0.xyz, extract _inputs0 as dependency
        dependencies = [x.split('.')[0] for x in dependencies]
        return list(set(dependencies))

    def input(self, message: Any) -> Any:
        # Hydrate the input and config before processing
        try:
            self._input = hydrate_input(
                self._input, message) if message else self._input
            self._config = hydrate_input(
                self._config, message) if self._config else self._config
            output = self.process()
        except Exception as e:
            output = {
                'errors': [str(e)], 'raw_response': {
                    'text': str(e),
                    'status_code': 400,
                },
            }

            # Send error to output stream
            self._output_stream.error(e)

        bookkeeping_data = self.get_bookkeeping_data()
        if not bookkeeping_data:
            bookkeeping_data = BookKeepingData(
                input=self._input, config=self._config, output=output or {}, session_data=self.session_data_to_persist(), timestamp=time.time(),
            )

        self._output_stream.bookkeep(bookkeeping_data)

    def input_stream(self, message: Any) -> Any:
        # We do not support input stream for this processor
        pass
