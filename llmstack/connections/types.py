import copy
from llmstack.connections.models import ConnectionStatus
from pydantic import BaseModel
from typing import Generic, Iterator, TypeVar
from django.conf import settings
from llmstack.common.utils.module_loader import get_all_sub_classes


def get_connection_type_interface_subclasses():
    subclasses = []
    allowed_packages = [
        'llmstack.connections.handlers',
    ]

    excluded_packages = []

    try:
        import jnpr.junos
    except:
        excluded_packages.append('llmstack.connections.handlers.junos_login')

    for package in allowed_packages:
        subclasses_in_package = get_all_sub_classes(
            package, ConnectionTypeInterface)

        for subclass in subclasses_in_package:
            if subclass.__module__ not in excluded_packages:
                subclasses.append(subclass)

    return subclasses


ConnectionConfigurationSchemaType = TypeVar(
    'ConnectionConfigurationSchemaType')


class BaseSchema(BaseModel):
    pass

    """
    This is Base Schema model for all the connection configuration types.
    """
    @ classmethod
    def get_json_schema(cls):
        return super().schema_json(indent=2)

    @ classmethod
    def get_schema(cls):
        return super().schema()

    # TODO: This is a copy of the same method in DataSourceTypeInterface. Refactor to a common place.
    @ classmethod
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
                        elif schema[key][prop_key]['type'] == 'string':
                            ui_schema[key][prop_key]['ui:widget'] = 'text'
                        elif schema[key][prop_key]['type'] == 'integer' or schema[key][prop_key]['type'] == 'number':
                            ui_schema[key][prop_key]['ui:widget'] = 'updown'
                        elif schema[key][prop_key]['type'] == 'boolean':
                            ui_schema[key][prop_key]['ui:widget'] = 'checkbox'
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
                        'advanced_parameter', False,
                    )
            else:
                ui_schema[key] = copy.deepcopy(schema[key])
        return ui_schema['properties']


class ConnectionTypeInterface(Generic[ConnectionConfigurationSchemaType]):
    """Interface for connection types."""
    @staticmethod
    def slug() -> str:
        raise NotImplementedError

    @staticmethod
    def provider_slug() -> str:
        raise NotImplementedError

    @staticmethod
    def name() -> str:
        raise NotImplementedError

    @staticmethod
    def description() -> str:
        raise NotImplementedError

    @classmethod
    def parse_config(cls, config: dict) -> ConnectionConfigurationSchemaType:
        connection_type_interface = cls.__orig_bases__[0]
        return connection_type_interface.__args__[0].parse_obj(config)

    def activate(self, connection) -> Iterator[str]:
        # Establish connection and persist any connection artifacts
        raise NotImplementedError

    @classmethod
    def get_config_schema(cls) -> ConnectionConfigurationSchemaType:
        connection_type_interface = cls.__orig_bases__[0]
        return connection_type_interface.__args__[0].get_schema()

    @classmethod
    def get_config_ui_schema(cls) -> dict:
        connection_type_interface = cls.__orig_bases__[0]
        return connection_type_interface.__args__[0].get_ui_schema()


class ConnectionTypeFactory:
    """
    Factory class for Data source types
    """
    @staticmethod
    def get_connection_type_handler(connection_type_slug, provider_slug) -> ConnectionTypeInterface:
        subclasses = get_connection_type_interface_subclasses()
        for subclass in subclasses:
            # Convert to lowercase to avoid case sensitivity
            if subclass.slug() == connection_type_slug and subclass.provider_slug() == provider_slug:
                return subclass
        return None
