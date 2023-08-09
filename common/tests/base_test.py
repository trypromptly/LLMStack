import unittest
from enum import Enum
from typing import Generic

from common.promptly.core.base import BaseConfiguration
from common.promptly.core.base import BaseConfigurationType
from common.promptly.core.base import BaseInput
from common.promptly.core.base import BaseInputType
from common.promptly.core.base import BaseOutput
from common.promptly.core.base import BaseOutputType
from common.promptly.core.base import BaseProcessor


class TestProcessorInput(BaseInput):
    name: str


class TestProcessorOutput(BaseOutput):
    answer: str


class TestProcessorConfiguration(BaseConfiguration):
    style: str


class TestProcessor(BaseProcessor[TestProcessorInput, TestProcessorOutput, TestProcessorConfiguration], Generic[BaseInputType, BaseOutputType, BaseConfigurationType]):
    @staticmethod
    def name() -> str:
        return 'TestProcessor'

    def _process(self, input: TestProcessorInput, configuration: TestProcessorConfiguration) -> BaseOutputType:
        if self.configuration.style == 'lower':
            return TestProcessorOutput(answer=input.name.lower())
        elif self.configuration.style == 'upper':
            return TestProcessorOutput(answer=input.name.upper())
        elif self.configuration.style == 'capitalize':
            return self.TestProcessorOutput(answer=input.name.capitalize())
        else:
            raise Exception('Invalid style')


class TestBaseProcessor(unittest.TestCase):

    def test_name(self):
        self.assertEqual(TestProcessor.name(), 'TestProcessor')

    def test_input_schema(self):
        schema = """{"title": "TestProcessorInput", "type": "object", "properties": {"_env": {"title": " Env", "description": "Environment variables (metadata) to be passed with input", "allOf": [{"$ref": "#/definitions/BaseInputEnvironment"}]}, "name": {"title": "Name", "type": "string"}}, "required": ["name"], "definitions": {"BaseInputEnvironment": {"title": "BaseInputEnvironment", "type": "object", "properties": {"bypass_cache": {"title": "Bypass Cache", "description": "Bypass cache", "default": true, "type": "boolean"}}}}}"""
        self.assertEqual(TestProcessor.get_input_schema(), schema)

    def test_output_schema(self):
        schema = """{"title": "TestProcessorOutput", "type": "object", "properties": {"metadata": {"title": "Metadata", "description": "Metadata", "default": {}, "allOf": [{"$ref": "#/definitions/BaseSchema"}]}, "answer": {"title": "Answer", "type": "string"}}, "required": ["answer"], "definitions": {"BaseSchema": {"title": "BaseSchema", "type": "object", "properties": {}}}}"""        # self.assertEqual(TestProcessor.get_output_schema(), schema)
        self.assertEqual(TestProcessor.get_output_schema(), schema)

    def test_configuration_schema(self):
        schema = """{"title": "TestProcessorConfiguration", "type": "object", "properties": {"style": {"title": "Style", "type": "string"}}, "required": ["style"]}"""
        self.assertEqual(TestProcessor.get_configuration_schema(), schema)

    def test_process(self):
        input = TestProcessorInput(name='test')
        configuration = TestProcessorConfiguration(style='lower')
        output = TestProcessor(
            configuration=configuration.dict(),
        ).process(input=input.dict())
        expected_output = TestProcessorOutput(answer='test')
        self.assertEqual(output.answer, expected_output.answer)

    def test_exception(self):
        input = TestProcessorInput(name='test')
        configuration = TestProcessorConfiguration(style='invalid')
        with self.assertRaises(Exception) as context:
            output = TestProcessor(
                configuration=configuration.dict(),
            ).process(input=input.dict())


if __name__ == '__main__':
    unittest.main()
