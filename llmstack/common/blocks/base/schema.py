from pydantic import BaseModel
from pydantic.json_schema import GenerateJsonSchema


def custom_json_dumps(v, **kwargs):
    import ujson as json

    default_arg = kwargs.get("default", None)
    return json.dumps(v, default=default_arg)


def custom_json_loads(v, **kwargs):
    import ujson as json

    return json.loads(v, **kwargs)


def get_ui_schema_from_json_schema(json_schema):
    """
    This function receives a json schema and returns a UI schema
    """

    def form_ui_per_prop(p_key, prop_schema_dict):
        """
        This functions receives the property key and its schema dictionary
        It checks the type of the property value and based on its type,
        assigns the correct UI widget and other UI properties to it
        """
        ui_prop = {}

        if "title" in prop_schema_dict:
            ui_prop["ui:label"] = prop_schema_dict["title"]

        if "description" in prop_schema_dict:
            ui_prop["ui:description"] = prop_schema_dict["description"]

        type_val = prop_schema_dict.get("type")

        if type_val == "string":
            ui_prop["ui:widget"] = "text"
        elif type_val in ("integer", "number"):
            if "minimum" in prop_schema_dict and "maximum" in prop_schema_dict:
                ui_prop["ui:widget"] = "range"
                ui_prop["ui:options"] = {
                    "min": prop_schema_dict["minimum"],
                    "max": prop_schema_dict["maximum"],
                }
            else:
                ui_prop["ui:widget"] = "updown"
        elif type_val == "boolean":
            ui_prop["ui:widget"] = "checkbox"
        elif "enum" in prop_schema_dict:
            ui_prop["ui:widget"] = "select"
            ui_prop["ui:options"] = {
                "enumOptions": [{"value": val, "label": val} for val in prop_schema_dict["enum"]],
            }

        if "widget" in prop_schema_dict:
            ui_prop["ui:widget"] = prop_schema_dict["widget"]

        if "options" in prop_schema_dict:
            ui_prop["ui:options"] = {
                "enumOptions": [{"value": val, "label": val} for val in prop_schema_dict["options"]],
                "values": prop_schema_dict["options"],
            }

        if prop_schema_dict.get("format") == "date-time":
            ui_prop["ui:widget"] = "datetime"

        # Unless explicitly mentioned, all properties are advanced parameters
        ui_prop["ui:advanced"] = prop_schema_dict.get(
            "advanced_parameter",
            True,
        )

        return ui_prop

    ui_schema = {
        "ui:order": list(json_schema["properties"].keys()),
        "properties": {},
    }

    for p_key, p_val in json_schema["properties"].items():
        ui_schema["properties"][p_key] = form_ui_per_prop(p_key, p_val)

    return ui_schema["properties"]


class CustomGenerateJsonSchema(GenerateJsonSchema):
    def nullable_schema(self, schema):
        # Source: https://github.com/pydantic/pydantic/issues/7161#issuecomment-1840346757
        null_schema = {"type": "null"}
        inner_json_schema = self.generate_inner(schema["schema"])

        if inner_json_schema == null_schema:
            return null_schema
        else:
            # Thanks to the equality check against `null_schema` above, I think 'oneOf' would also be valid here;
            # I'll use 'anyOf' for now, but it could be changed it if it would work better with some external tooling
            flattened_anyof = self.get_flattened_anyof([inner_json_schema, null_schema])
            if len(flattened_anyof["anyOf"]) == 2:
                return inner_json_schema
            return flattened_anyof


class BaseSchema(BaseModel):
    @classmethod
    def get_json_schema(cls):
        return custom_json_dumps(cls.get_schema(), indent=2)

    @classmethod
    def get_schema(cls):
        schema = super().model_json_schema(schema_generator=CustomGenerateJsonSchema)
        if "title" in schema:
            # Convert camel case to title case
            schema["title"] = (
                "".join(" " + char if char.isupper() else char for char in schema["title"]).strip().title()
            )

        return schema

    @classmethod
    def get_ui_schema(cls):
        """
        This function receives a class method; gets the schema of the class
        Calls the function form_ui_per_prop to form the dictionary of UI schema values
        The resultant UI Schema only contains the properties
        """
        return get_ui_schema_from_json_schema(cls.get_schema())
