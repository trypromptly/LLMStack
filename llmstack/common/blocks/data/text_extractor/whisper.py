from pydantic import root_validator

from llmstack.common.blocks.base.processor import ProcessorInterface
from llmstack.common.blocks.data import DataDocument
from llmstack.common.blocks.data.text_extractor import TextExtractorInput, TextExtractorOutput, TextExtractorConfiguration
from llmstack.common.utils.text_extract import extract_text_elements, ExtraParams


class WhisperTextExtractorInput(TextExtractorInput):
    openai_api_key: str

    @classmethod
    @root_validator()
    def validate(cls, field_values):
        mime_type = field_values.get('mime_type')
        openai_api_key = field_values.get('openai_api_key')
        if mime_type not in [
            'audio/mp3',
            'audio/mpeg',
            'audio/wav',
            'video/mp4',
            'video/mpeg',
                'video/webm']:
            raise ValueError('Mime type is not supported')
        if not openai_api_key:
            raise ValueError('OpenAI API key is required')
        return field_values


class WhisperTextExtractorProcessor(
        ProcessorInterface[WhisperTextExtractorInput, TextExtractorOutput, TextExtractorConfiguration]):
    def process(
            self,
            input: WhisperTextExtractorInput,
            configuration: TextExtractorConfiguration) -> TextExtractorOutput:
        elements = extract_text_elements(
            mime_type=input.mime_type,
            data=input.data,
            file_name=input.id,
            extra_params=ExtraParams(
                openai_key=input.openai_api_key))
        return TextExtractorOutput(
            documents=list(map(lambda element: DataDocument(
                content=element.text,
                content_text=element.text,
                metadata={
                    "mime_type": input.mime_type,
                    "file_name": input.id,
                    **element.metadata.__dict__
                }
            ), elements))
        )
