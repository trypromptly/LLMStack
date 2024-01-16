from pydantic import BaseModel

from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface


class PredictInput(BaseModel):
    input: dict


class PredictOutput(BaseModel):
    output: dict


class PredictConfiguration(BaseModel):
    model: str
    version: str


class Predict(
        ApiProcessorInterface[PredictInput, PredictOutput, PredictConfiguration]):

    def name() -> str:
        return 'replicate/predict'

    def process(self, input: dict) -> dict:
        raise Exception()
