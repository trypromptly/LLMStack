import os
import unittest

from llmstack.common.blocks.llm.stabilityai import (
    StabilityAIGrpcInputEnvironment,
    StabilityAIGrpcProcessorConfiguration,
    StabilityAIText2ImageGrpcProcessor,
    StabilityAIText2ImageGrpcProcessorInput,
)


class StabilityAIText2ImageGrpcProcessorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.api_key = os.environ.get("STABILITY_AI_API_KEY")

    def test_name_text2image(self):
        self.assertEqual(
            StabilityAIText2ImageGrpcProcessor.name(),
            "stability_ai_text2image",
        )

    def test_valid_text2image(self):
        result = StabilityAIText2ImageGrpcProcessor(
            configuration=StabilityAIGrpcProcessorConfiguration().dict(),
        ).process(
            input=StabilityAIText2ImageGrpcProcessorInput(
                prompt=["apple"],
                env=StabilityAIGrpcInputEnvironment(
                    stability_ai_api_key=self.api_key,
                ),
            ).dict(),
        )

        self.assertTrue(len(result.answer) > 0)


if __name__ == "__main__":
    unittest.main()
