import unittest

from pydantic import BaseModel

from llmstack.common.blocks.base.processor import (BaseConfiguration,
                                                   BaseConfigurationType,
                                                   BaseInput, BaseInputType,
                                                   BaseOutput, BaseOutputType,
                                                   BaseProcessor,
                                                   ProcessorInterface)


class TestInputModel(BaseModel):
    pass


class TestOutputModel(BaseModel):
    pass


class TestConfigurationModel(BaseModel):
    pass


class TestProcessor(
    BaseProcessor[TestInputModel, TestOutputModel, TestConfigurationModel],
):
    @staticmethod
    def name() -> str:
        return "Test Processor"

    @staticmethod
    def slug() -> str:
        return "test_processor"

    @staticmethod
    def description() -> str:
        return "Test Processor"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    def process(self, input: dict) -> TestOutputModel:
        pass


class TestProcessorTestCase(unittest.TestCase):
    def test_name(self):
        self.assertEqual(TestProcessor.name(), "Test Processor")

    def test_slug(self):
        self.assertEqual(TestProcessor.slug(), "test_processor")

    def test_get_input_cls(self):
        self.assertEqual(TestProcessor.get_input_cls(), TestInputModel)

    def test_get_output_cls(self):
        self.assertEqual(TestProcessor.get_output_cls(), TestOutputModel)

    def test_get_configuration_cls(self):
        self.assertEqual(
            TestProcessor.get_configuration_cls(),
            TestConfigurationModel,
        )

    def test_get_input_schema(self):
        self.assertEqual(
            TestProcessor.get_input_schema(),
            TestInputModel.schema_json(),
        )

    def test_get_output_schema(self):
        self.assertEqual(
            TestProcessor.get_output_schema(),
            TestOutputModel.schema_json(),
        )

    def test_get_configuration_schema(self):
        self.assertEqual(
            TestProcessor.get_configuration_schema(),
            TestConfigurationModel.schema_json(),
        )


class TestProcessor1Input(BaseInput):
    name: str


class TestProcessor1Output(BaseOutput):
    answer: str


class TestProcessor1Configuration(BaseConfiguration):
    style: str


class TestProcessor1(
    ProcessorInterface[TestProcessor1Input, TestProcessor1Output, TestProcessor1Configuration],
):
    @staticmethod
    def name() -> str:
        return "TestProcessor"

    def process(
        self,
        input: TestProcessor1Input,
        configuration: TestProcessor1Configuration,
    ) -> BaseOutputType:
        if configuration.style == "lower":
            return TestProcessor1Output(answer=input.name.lower())
        elif configuration.style == "upper":
            return TestProcessor1Output(answer=input.name.upper())
        elif configuration.style == "capitalize":
            return TestProcessor1Output(answer=input.name.capitalize())
        else:
            raise Exception("Invalid style")


class ProcessorInterfaceTestCase(unittest.TestCase):
    def test_name(self):
        self.assertEqual(TestProcessor1.name(), "TestProcessor")

    def test_input_schema(self):
        schema = """{"title":"TestProcessor1Input","type":"object","properties":{"_env":{"title":" Env","description":"Environment variables (metadata) to be passed with input","allOf":[{"$ref":"#\\/definitions\\/BaseInputEnvironment"}]},"name":{"title":"Name","type":"string"}},"required":["name"],"definitions":{"BaseInputEnvironment":{"title":"BaseInputEnvironment","type":"object","properties":{"bypass_cache":{"title":"Bypass Cache","description":"Bypass cache","default":true,"type":"boolean"}}}}}"""
        self.assertEqual(TestProcessor1.get_input_schema(), schema)

    def test_output_schema(self):
        schema = """{"title":"TestProcessor1Output","type":"object","properties":{"metadata":{"title":"Metadata","description":"Metadata","default":{},"allOf":[{"$ref":"#\\/definitions\\/BaseSchema"}]},"answer":{"title":"Answer","type":"string"}},"required":["answer"],"definitions":{"BaseSchema":{"title":"BaseSchema","type":"object","properties":{}}}}"""
        self.assertEqual(TestProcessor1.get_output_schema(), schema)

    def test_configuration_schema(self):
        schema = """{"title":"TestProcessor1Configuration","type":"object","properties":{"style":{"title":"Style","type":"string"}},"required":["style"]}"""
        self.assertEqual(TestProcessor1.get_configuration_schema(), schema)

    def test_process(self):
        input = TestProcessor1Input(name="test")
        configuration = TestProcessor1Configuration(style="lower")
        output = TestProcessor1().process(input=input, configuration=configuration)
        expected_output = TestProcessor1Output(answer="test")
        self.assertEqual(output.answer, expected_output.answer)

    def test_exception(self):
        input = TestProcessor1Input(name="test")
        configuration = TestProcessor1Configuration(style="invalid")
        with self.assertRaises(Exception) as context:
            output = TestProcessor1().process(input=input, configuration=configuration)


if __name__ == "__main__":
    unittest.main()
