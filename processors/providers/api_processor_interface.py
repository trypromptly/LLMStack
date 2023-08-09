import abc
import copy
import logging
import time
from enum import Enum
from typing import Any
from typing import Dict
from typing import Generic
from typing import Type
from typing import TypeVar

import ujson as json
from pydantic import AnyUrl
from pydantic import BaseModel

from common.utils.utils import hydrate_input
from play.actor import Actor
from play.actor import BookKeepingData
from play.utils import extract_jinja2_variables

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


def custom_json_dumps(v, **kwargs):
    default_arg = kwargs.get('default', None)
    return json.dumps(v, default=default_arg)


def custom_json_loads(v, **kwargs):
    return json.loads(v, **kwargs)


class BaseSchema(BaseModel):
    class Config:
        json_dumps = custom_json_dumps
        json_loads = custom_json_loads
    """
    This is Base Schema model for all API processor schemas
    """
    @classmethod
    def get_json_schema(cls):
        return cls.schema_json(indent=2)

    @classmethod
    def get_schema(cls):
        return cls.schema()

    @classmethod
    def get_ui_schema(cls):
        schema = cls.get_schema()
        ui_schema = {}
        for key in schema.keys():
            if key == 'properties':
                ui_schema['ui:order'] = list(schema[key].keys())
                ui_schema[key] = {}
                for prop_key in schema[key].keys():
                    ui_schema[key][prop_key] = {}
                    if 'title' in schema[key][prop_key]:
                        ui_schema[key][prop_key]['ui:label'] = schema[key][prop_key]['title']
                    if 'description' in schema[key][prop_key]:
                        ui_schema[key][prop_key]['ui:description'] = schema[key][prop_key]['description']
                    if 'type' in schema[key][prop_key]:
                        if schema[key][prop_key]['type'] == 'string' and prop_key in ('data', 'text', 'content'):
                            ui_schema[key][prop_key]['ui:widget'] = 'textarea'
                        elif schema[key][prop_key]['type'] == 'string' and 'format' not in schema[key][prop_key]:
                            ui_schema[key][prop_key]['ui:widget'] = 'text'
                        elif schema[key][prop_key]['type'] == 'integer' or schema[key][prop_key]['type'] == 'number':
                            if 'minimum' in schema[key][prop_key] and 'maximum' in schema[key][prop_key]:
                                ui_schema[key][prop_key]['ui:widget'] = 'range'
                                ui_schema[key][prop_key]['ui:options'] = {
                                    'min': schema[key][prop_key]['minimum'], 'max': schema[key][prop_key]['maximum'],
                                }
                            else:
                                ui_schema[key][prop_key]['ui:widget'] = 'updown'
                        elif schema[key][prop_key]['type'] == 'boolean':
                            ui_schema[key][prop_key]['ui:widget'] = 'checkbox'
                        # elif schema[key][prop_key]['type'] == 'array':
                        #     ui_schema[key][prop_key]['ui:widget'] = 'array'
                    if 'enum' in schema[key][prop_key]:
                        ui_schema[key][prop_key]['ui:widget'] = 'select'
                        ui_schema[key][prop_key]['ui:options'] = {
                            'enumOptions': [
                                {'value': val, 'label': val} for val in schema[key][prop_key]['enum']
                            ],
                        }
                    if 'widget' in schema[key][prop_key]:
                        ui_schema[key][prop_key]['ui:widget'] = schema[key][prop_key]['widget']
                    if 'format' in schema[key][prop_key] and schema[key][prop_key]['format'] == 'date-time':
                        ui_schema[key][prop_key]['ui:widget'] = 'datetime'
                    ui_schema[key][prop_key]['ui:advanced'] = schema[key][prop_key].get(
                        'advanced_parameter', True,
                    )
            else:
                ui_schema[key] = copy.deepcopy(schema[key])
        return ui_schema['properties']


class ApiProcessorInterface(Generic[InputSchemaType, OutputSchemaType, ConfigurationSchemaType], Actor):
    """
    Abstract class for API processors
    """

    def __init__(self, input, config, env, output_stream=None, dependencies=[], session_data=None):
        super().__init__(dependencies=dependencies)

        # TODO: This is for backward compatibility. Remove this once all the processors are updated
        if 'datasource' in config and isinstance(config['datasource'], str):
            config['datasource'] = [config['datasource']]
        if 'datasources' in config and isinstance(config['datasources'], str):
            config['datasources'] = [config['datasources']]

        configuration_cls = self.__class__.__orig_bases__[0].__args__[2]
        input_cls = self.__class__.__orig_bases__[0].__args__[0]
        self._config = configuration_cls(**config)
        self._input = input_cls(**input)
        self._env = env
        self._output_stream = output_stream

        self.process_session_data(session_data)

    @staticmethod
    def name() -> str:
        raise NotImplementedError

    @staticmethod
    def slug() -> str:
        raise NotImplementedError

    @classmethod
    def get_configuration_schema(cls) -> dict:
        api_processor_interface_class = cls.__orig_bases__[0]
        return api_processor_interface_class.__args__[2].get_json_schema()

    @classmethod
    def get_configuration_ui_schema(cls) -> dict:
        api_processor_interface_class = cls.__orig_bases__[0]
        return api_processor_interface_class.__args__[2].get_ui_schema()

    @classmethod
    def get_input_schema(cls) -> dict:
        api_processor_interface_class = cls.__orig_bases__[0]
        return api_processor_interface_class.__args__[0].get_json_schema()

    @classmethod
    def get_input_ui_schema(cls) -> dict:
        api_processor_interface_class = cls.__orig_bases__[0]
        return api_processor_interface_class.__args__[0].get_ui_schema()

    @classmethod
    def get_output_schema(cls) -> dict:
        api_processor_interface_class = cls.__orig_bases__[0]
        schema = json.loads(
            api_processor_interface_class.__args__[
                1
            ].get_json_schema(),
        )
        if 'description' in schema:
            del schema['description']
        if 'title' in schema:
            del schema['title']
        if 'api_response' in schema['properties']:
            del schema['properties']['api_response']

        for key in schema['properties'].keys():
            if 'title' in schema['properties'][key]:
                del schema['properties'][key]['title']

        return json.dumps(schema)

    @classmethod
    def get_output_ui_schema(cls) -> dict:
        api_processor_interface_class = cls.__orig_bases__[0]
        ui_schema = api_processor_interface_class.__args__[1].get_ui_schema()
        ui_schema = {}
        schema = api_processor_interface_class.__args__[
            1
        ].get_schema()
        for key in schema['properties'].keys():
            if 'widget' in schema['properties'][key]:
                ui_schema[key] = {
                    'ui:widget': schema['properties'][key]['widget'],
                }
        ui_schema['ui:submitButtonOptions'] = {
            'norender': True,
        }

        return ui_schema

    @classmethod
    def get_output_cls(cls) -> Type[BaseSchema]:
        api_processor_interface_class = cls.__orig_bases__[0]
        return api_processor_interface_class.__args__[1]

    @abc.abstractmethod
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
        elif isinstance(result, BaseSchema):
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
            self._input = hydrate_input(self._input, message)
            self._config = hydrate_input(self._config, message)
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
