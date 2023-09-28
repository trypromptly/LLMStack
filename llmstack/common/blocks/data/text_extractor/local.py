from llmstack.common.blocks.base.processor import ProcessorInterface
from llmstack.common.blocks.data import DataDocument
from llmstack.common.blocks.data.text_extractor import TextExtractorInput, TextExtractorOutput,  TextExtractorConfiguration
from llmstack.common.utils.text_extract import extract_text_elements, ExtraParams


class LocalTextExtractorProcessor(ProcessorInterface[TextExtractorInput, TextExtractorOutput, TextExtractorConfiguration]):
    @staticmethod
    def name() -> str:
        return "local_text_extractor"

    @staticmethod
    def slug() -> str:
        return "text_extractor"

    @staticmethod
    def description() -> str:
        return "Extracts text from a file"

    @staticmethod
    def provider_slug() -> str:
        return 'promptly'

    def process(self, input: TextExtractorInput, configuration: TextExtractorConfiguration) -> TextExtractorOutput:

        elements = extract_text_elements(
            mime_type=input.mime_type, data=input.data, file_name=input.id, extra_params=ExtraParams(),
        )
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
