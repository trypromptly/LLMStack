import logging
import base64
import re
import requests
from typing import Dict
from common.blocks.base.processor import ProcessorInterface
from common.blocks.data.source import DataSourceInputSchema, DataSourceConfigurationSchema, DataSourceOutputSchema
from pydantic import root_validator
from common.utils.text_extract import is_youtube_video_url, get_url_content_type, run_url_spider_in_process
from common.blocks.data.text_extractor.local import LocalTextExtractorProcessor
from common.blocks.data.text_extractor.whisper import WhisperTextExtractorProcessor, WhisperTextExtractorInput 
from common.blocks.data.text_extractor import TextExtractorInput

logger = logging.getLogger(__name__)

def validate_parse_data_uri(data_uri, data_uri_regex=r'data:(?P<mime>[\w/\-\.]+);name=(?P<filename>.*);base64,(?P<data>[\s\S]*)'):
    pattern = re.compile(data_uri_regex)
    match = pattern.match(data_uri)
    if not match:
        raise Exception('Invalid data URI')

    mime_type, file_name, data = match.groups()
    return (mime_type, file_name, data)

class UriInput(DataSourceInputSchema):
    uri: str
    
    @root_validator()
    @classmethod
    def validate_url(cls, field_values) -> str:
        value = field_values.get("uri")
        # Ensure that the URL is valid and that it is an HTTP URL or Data URL
        if not value.startswith("http://") and not value.startswith("https://") and not value.startswith("data:"):
            raise ValueError("URL must be an HTTP URL or Data URL")
        
        if value.startswith("data:"):
            mime_type, file_name, data = validate_parse_data_uri(value)
            if mime_type is None or file_name is None or data is None:
                raise ValueError("Data URI must be valid")
            
        return field_values

class UriConfiguration(DataSourceConfigurationSchema):
    # The text extractor to use for the given mime type
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
    default_timeout: int = 60
    headers: Dict = {
    'User-Agent': 'Mozilla/5.0 (X11; Windows; Windows x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36',
    }
    use_scrapy: bool = False
    
    
class Uri(ProcessorInterface[UriInput, DataSourceOutputSchema, UriConfiguration]):
    def _extract_text(self, data: bytes, mime_type: str, file_name: str, configuration: UriConfiguration) -> DataSourceOutputSchema:
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
                data=data,
                mime_type=mime_type,
                id=file_name),
                configuration=None
            )
            return DataSourceOutputSchema(
                documents=result.documents)
        else:
            raise Exception("Invalid mime type")
        
    def process_data_url(self, input: UriInput, configuration: UriConfiguration) -> DataSourceOutputSchema:
        mime_type, file_name, base64_encoded_data = validate_parse_data_uri(input.uri)
        decoded_data = base64.b64decode(base64_encoded_data)
        return self._extract_text(decoded_data, mime_type, file_name, configuration)
        
    
    def process_http_url(self, input: UriInput, configuration: UriConfiguration) -> DataSourceOutputSchema:
        data = None
        if is_youtube_video_url(input.uri):
            raise Exception("Youtube video URLs are not supported")

        url_content_type = get_url_content_type(url=input.uri)
        url_content_type_parts = url_content_type.split(';')
        mime_type = url_content_type_parts[0]
        url_content_type_args = {}

        for part in url_content_type_parts[1:]:
            key, value = part.split('=')
            url_content_type_args[
                key.strip().rstrip()
            ] = value.strip().rstrip().lower()

        if mime_type == 'text/html':
            # If this is an html page and we are configured to use scrapy
            if configuration.use_scrapy:
                result = run_url_spider_in_process(url=input.uri, use_renderer=True)
                data = result[0]['html_page'].encode('utf-8')
            else:
                data = requests.get(url=input.uri, headers=configuration.headers,
                    timeout=configuration.default_timeout,
                ).content
        else:
            data = requests.get(url=input.uri, headers=configuration.headers, timeout=configuration.default_timeout).content

        return self._extract_text(data, mime_type, input.uri, configuration)
        
    
    def process(self, input: UriInput, configuration: UriConfiguration) -> DataSourceOutputSchema:
        if input.uri.startswith("data:"):
            return self.process_data_url(input, configuration)
        elif input.uri.startswith("http://") or input.uri.startswith("https://"):
            return self.process_http_url(input, configuration)
        else:
            raise Exception("Invalid URI")