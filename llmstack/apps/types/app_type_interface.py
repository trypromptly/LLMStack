import copy
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

AppConfigurationSchemaType = TypeVar("AppConfigurationSchemaType")


class BaseSchema(BaseModel):
    pass

    """
    This is Base Schema model for all app type schemas
    """

    @classmethod
    def get_json_schema(cls):
        return super().schema_json(indent=2)

    @classmethod
    def get_schema(cls):
        return super().schema()

    # TODO: This is a copy of the same method in DataSourceTypeInterface.
    # Refactor to a common place.
    @classmethod
    def get_ui_schema(cls):
        schema = cls.get_schema()
        ui_schema = {}
        for key in schema.keys():
            if key == "properties":
                ui_schema["ui:order"] = list(schema[key].keys())
                ui_schema[key] = {}
                for prop_key in schema[key].keys():
                    ui_schema[key][prop_key] = {}
                    if "title" in schema[key][prop_key]:
                        ui_schema[key][prop_key]["ui:label"] = schema[key][prop_key]["title"]
                    if "description" in schema[key][prop_key]:
                        ui_schema[key][prop_key]["ui:description"] = schema[key][prop_key]["description"]
                    if "type" in schema[key][prop_key]:
                        if schema[key][prop_key]["type"] == "string" and prop_key in (
                            "data",
                            "text",
                            "content",
                        ):
                            ui_schema[key][prop_key]["ui:widget"] = "textarea"
                        elif schema[key][prop_key]["type"] == "string":
                            ui_schema[key][prop_key]["ui:widget"] = "text"
                        elif schema[key][prop_key]["type"] == "integer" or schema[key][prop_key]["type"] == "number":
                            ui_schema[key][prop_key]["ui:widget"] = "updown"
                        elif schema[key][prop_key]["type"] == "boolean":
                            ui_schema[key][prop_key]["ui:widget"] = "checkbox"
                    if "enum" in schema[key][prop_key]:
                        ui_schema[key][prop_key]["ui:widget"] = "select"
                        ui_schema[key][prop_key]["ui:options"] = {
                            "enumOptions": [{"value": val, "label": val} for val in schema[key][prop_key]["enum"]],
                        }
                    if "widget" in schema[key][prop_key]:
                        ui_schema[key][prop_key]["ui:widget"] = schema[key][prop_key]["widget"]
                    if "format" in schema[key][prop_key] and schema[key][prop_key]["format"] == "date-time":
                        ui_schema[key][prop_key]["ui:widget"] = "datetime"
                    ui_schema[key][prop_key]["ui:advanced"] = schema[key][prop_key].get(
                        "advanced_parameter",
                        False,
                    )
            else:
                ui_schema[key] = copy.deepcopy(schema[key])
        return ui_schema["properties"]


class AppTypeInterface(Generic[AppConfigurationSchemaType]):
    """
    This is the interface for all app types.
    """

    @staticmethod
    def slug(self) -> str:
        raise NotImplementedError

    @staticmethod
    def name(self) -> str:
        raise NotImplementedError

    @staticmethod
    def description(self) -> str:
        raise NotImplementedError

    @classmethod
    def get_config_schema(cls) -> AppConfigurationSchemaType:
        app_type_interface = cls.__orig_bases__[0]
        return app_type_interface.__args__[0].get_schema()

    @classmethod
    def get_config_ui_schema(cls) -> AppConfigurationSchemaType:
        app_type_interface = cls.__orig_bases__[0]
        return app_type_interface.__args__[0].get_ui_schema()

    @classmethod
    def pre_save(self, app):
        return app

    @classmethod
    def verify_request_signature(
        cls,
        app: Any,
        headers: dict,
        raw_body: bytes,
    ):
        return True
