from llmstack.common.blocks.base.schema import get_ui_schema_from_json_schema


class UnstructuredIOTransformers:
    @classmethod
    def get_schema(cls):
        json_schema = cls.schema()
        json_schema["properties"].pop("callback_manager", None)
        json_schema["properties"].pop("class_name", None)
        json_schema["properties"].pop("include_metadata", None)
        json_schema["properties"].pop("include_prev_next_rel", None)
        return json_schema

    @classmethod
    def get_ui_schema(cls):
        return get_ui_schema_from_json_schema(cls.get_schema())

    @classmethod
    def get_default_data(cls):
        data = cls().dict()
        data.pop("callback_manager", None)
        data.pop("class_name", None)
        data.pop("include_metadata", None)
        data.pop("include_prev_next_rel", None)
        return data
