import json
import unittest
from enum import Enum
from typing import Dict, List

from pydantic import Field

from llmstack.common.blocks.base.schema import BaseSchema


class TestEnum(Enum):
    TEST1 = "test1"
    TEST2 = "test2"


class NestedModel(BaseSchema):
    test: TestEnum = TestEnum.TEST1


class TestSchema(BaseSchema):
    test_str: str = "test"
    test_int: int = 1
    test_float: float = 1.0
    test_bool: bool = True
    test_list: List = ["test"]
    test_dict: Dict = {"test": "test"}
    test_int_range: int = Field(
        1,
        ge=0,
        le=10,
        description="test_int_range description",
    )
    test_textarea: str = Field("test", json_schema_extra={"widget": "textarea"})
    test_password: str = Field("test", json_schema_extra={"widget": "password"})
    test_non_advanced_parameter_str: str = Field(
        "test",
        json_schema_extra={"advanced_parameter": False},
    )

    test_enum: TestEnum = TestEnum.TEST1

    test_nested: NestedModel = NestedModel()


class TestBaseSchema(unittest.TestCase):
    def test_get_json_schema(self):
        test_schema = TestSchema()
        json_schema = json.loads(test_schema.get_json_schema())
        self.assertEqual(
            json_schema.get("properties")
            .get(
                "test_str",
            )
            .get("type"),
            "string",
        )
        self.assertEqual(
            json_schema.get("properties")
            .get(
                "test_int",
            )
            .get("type"),
            "integer",
        )
        self.assertEqual(
            json_schema.get("properties")
            .get(
                "test_float",
            )
            .get("type"),
            "number",
        )
        self.assertEqual(
            json_schema.get("properties")
            .get(
                "test_bool",
            )
            .get("type"),
            "boolean",
        )
        self.assertEqual(
            json_schema.get("properties")
            .get(
                "test_list",
            )
            .get("type"),
            "array",
        )
        self.assertEqual(
            json_schema.get("properties")
            .get(
                "test_dict",
            )
            .get("type"),
            "object",
        )
        self.assertEqual(
            json_schema.get("properties")
            .get(
                "test_int_range",
            )
            .get("type"),
            "integer",
        )
        self.assertEqual(
            json_schema.get("properties")
            .get(
                "test_textarea",
            )
            .get("type"),
            "string",
        )
        self.assertEqual(
            json_schema.get("properties")
            .get(
                "test_password",
            )
            .get("type"),
            "string",
        )
        self.assertEqual(
            json_schema.get("properties")
            .get(
                "test_non_advanced_parameter_str",
            )
            .get("type"),
            "string",
        )

    def test_get_schema(self):
        test_schema = TestSchema()
        schema = test_schema.get_schema()
        self.assertEqual(
            schema.get("properties")
            .get(
                "test_str",
            )
            .get("type"),
            "string",
        )
        self.assertEqual(
            schema.get("properties")
            .get(
                "test_int",
            )
            .get("type"),
            "integer",
        )
        self.assertEqual(
            schema.get("properties")
            .get(
                "test_float",
            )
            .get("type"),
            "number",
        )
        self.assertEqual(
            schema.get("properties")
            .get(
                "test_bool",
            )
            .get("type"),
            "boolean",
        )
        self.assertEqual(
            schema.get("properties")
            .get(
                "test_list",
            )
            .get("type"),
            "array",
        )
        self.assertEqual(
            schema.get("properties")
            .get(
                "test_dict",
            )
            .get("type"),
            "object",
        )
        self.assertEqual(
            schema.get("properties")
            .get(
                "test_int_range",
            )
            .get("type"),
            "integer",
        )
        self.assertEqual(
            schema.get("properties")
            .get(
                "test_textarea",
            )
            .get("type"),
            "string",
        )
        self.assertEqual(
            schema.get("properties")
            .get(
                "test_password",
            )
            .get("type"),
            "string",
        )
        self.assertEqual(
            schema.get("properties")
            .get(
                "test_non_advanced_parameter_str",
            )
            .get("type"),
            "string",
        )

    def test_get_ui_schema(self):
        test_schema = TestSchema()
        ui_schema = test_schema.get_ui_schema()
        self.assertEqual(ui_schema.get("test_str").get("ui:label"), "Test Str")
        self.assertEqual(ui_schema.get("test_str").get("ui:description"), None)

        self.assertEqual(ui_schema.get("test_str").get("ui:widget"), "text")
        self.assertEqual(ui_schema.get("test_int").get("ui:widget"), "updown")
        self.assertEqual(
            ui_schema.get(
                "test_int_range",
            ).get("ui:widget"),
            "range",
        )
        self.assertEqual(
            ui_schema.get("test_int_range")
            .get(
                "ui:options",
            )
            .get("min"),
            0,
        )
        self.assertEqual(
            ui_schema.get("test_int_range")
            .get(
                "ui:options",
            )
            .get("max"),
            10,
        )

        self.assertEqual(
            ui_schema.get(
                "test_float",
            ).get("ui:widget"),
            "updown",
        )
        self.assertEqual(
            ui_schema.get(
                "test_bool",
            ).get("ui:widget"),
            "checkbox",
        )
        self.assertEqual(ui_schema.get("test_list").get("ui:widget"), None)
        self.assertEqual(ui_schema.get("test_dict").get("ui:widget"), None)

        self.assertEqual(
            ui_schema.get("test_int_range").get(
                "ui:description",
            ),
            "test_int_range description",
        )

        self.assertEqual(
            ui_schema.get(
                "test_textarea",
            ).get("ui:widget"),
            "textarea",
        )
        self.assertEqual(
            ui_schema.get(
                "test_password",
            ).get("ui:widget"),
            "password",
        )

        self.assertEqual(ui_schema.get("test_str").get("ui:advanced"), True)
        self.assertEqual(
            ui_schema.get(
                "test_non_advanced_parameter_str",
            ).get("ui:advanced"),
            False,
        )
        self.assertEqual(
            ui_schema.get(
                "test_non_advanced_parameter_str",
            ).get("ui:widget"),
            "text",
        )


if __name__ == "__main__":
    unittest.main()
