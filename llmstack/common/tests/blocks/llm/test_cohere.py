import os
import unittest

from llmstack.common.blocks.llm.cohere import (
    CohereAPIInputEnvironment, CohereGenerateAPIProcessor,
    CohereGenerateAPIProcessorConfiguration, CohereGenerateAPIProcessorInput)


class CohereGenerateAPIProcessorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.api_key = os.environ.get("COHERE_API_KEY")

    def test_name_generate(self):
        self.assertEqual(
            CohereGenerateAPIProcessor.name(),
            "cohere_generate_api_processor",
        )

    def test_valid_generate(self):
        result = CohereGenerateAPIProcessor(
            configuration=CohereGenerateAPIProcessorConfiguration().dict(),
        ).process(
            input=CohereGenerateAPIProcessorInput(
                prompt="Hi",
                env=CohereAPIInputEnvironment(
                    cohere_api_key=self.api_key,
                ),
            ).dict(),
        )

        self.assertTrue(len(result.choices) > 0)


if __name__ == "__main__":
    unittest.main()
