import re
import magic
from pydantic import root_validator
from llmstack.common.blocks.base.processor import ProcessorInterface
from llmstack.common.blocks.data.source import DataSourceInputSchema, DataSourceConfigurationSchema, DataSourceOutputSchema
from llmstack.common.blocks.data.text_extractor.local import LocalTextExtractorProcessor
from llmstack.common.blocks.data.text_extractor.whisper import WhisperTextExtractorProcessor, WhisperTextExtractorInput
from llmstack.common.blocks.data.text_extractor import TextExtractorInput


class FileInput(DataSourceInputSchema):
    file: str

    @classmethod
    @root_validator()
    def validate_file(cls, field_values) -> str:
        value = field_values.get("file")
        # TODO: Validate that file is a valid file path and the file exists
        if not re.match(r"^[a-zA-Z0-9_\-\.\/]+$", value):
            raise ValueError("File must be a valid string")
        return value


class FileConfiguration(DataSourceConfigurationSchema):
    text_extractor: dict = {
        'application/csv': 'local',
        'application/epub+zip': 'local',
        'application/pdf': 'local',
        'application/rtf': 'local',
        'application/json': 'local',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'local',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'local',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'local',
        'application/msword': 'local',
        'application/vnd.ms-excel': 'local',
        'application/vnd.ms-powerpoint': 'local',
        'audio/mpeg': 'whisper',
        'audio/mp3': 'whisper',
        'image/jpeg': 'local',
        'image/png': 'local',
        'text/csv': 'local',
        'text/html': 'local',
        'text/markdown': 'local',
        'text/plain': 'local',
        'text/rtf': 'local',
        'video/mp4': 'whisper',
        'video/mpeg': 'whisper',
        'video/webm': 'whisper',
    }


class File(ProcessorInterface[FileInput,
                              DataSourceOutputSchema,
                              FileConfiguration]):
    def _extract_text(
            self,
            data: bytes,
            mime_type: str,
            file_name: str,
            configuration: FileConfiguration) -> DataSourceOutputSchema:
        if configuration.text_extractor.get(mime_type) == 'local':
            result = LocalTextExtractorProcessor().process(TextExtractorInput(
                data=data,
                mime_type=mime_type,
                id=file_name),
                configuration=None
            )
            return DataSourceOutputSchema(
                documents=result.documents)
        elif configuration.text_extractor.get(mime_type) == 'whisper':
            result = WhisperTextExtractorProcessor().process(WhisperTextExtractorInput(
                data=data, mime_type=mime_type, id=file_name), configuration=None)
            return DataSourceOutputSchema(
                documents=result.documents)
        else:
            raise Exception("Invalid mime type")

    def process(
            self,
            input: FileInput,
            configuration: FileConfiguration) -> DataSourceOutputSchema:

        with open(input.file, "r") as file_p:
            file_data = file_p.read()
            # Get the file mime type
            mime_type = magic.from_buffer(file_data, mime=True)
            return self._extract_text(
                file_data, mime_type, input.file, configuration)
