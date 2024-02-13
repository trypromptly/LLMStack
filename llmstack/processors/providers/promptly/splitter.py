import json
import logging
from typing import List, Literal, Union

from asgiref.sync import async_to_sync
from pydantic import BaseModel, Field

from llmstack.common.utils.splitter import CharacterTextSplitter, HtmlSplitter
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class BaseSplitter(BaseModel):
    chunk_size: int = Field(default=4000, description="Maximum size of each chunk")
    chunk_overlap: int = Field(default=0, description="Overlap between chunks")


class CharacterSplitter(BaseSplitter):
    type: Literal["text_splitter"] = "text_splitter"
    separator: str = Field(
        default="\n", description="Separator to split the input string. Default is newline character"
    )


class HTMLSplitter(BaseSplitter):
    type: Literal["html_splitter"] = "html_splitter"


class SplitterProcessorInput(ApiProcessorSchema):
    input_str: str = Field(default="", description="Input string to split", widget="textarea")


class SplitterProcessorOutput(ApiProcessorSchema):
    output_list: List[str]


class SplitterProcessorConfiguration(ApiProcessorSchema):
    splitter: Union[CharacterSplitter, HTMLSplitter] = Field(discriminator="type", advanced_parameter=False)


class SplitterProcessor(
    ApiProcessorInterface[SplitterProcessorInput, SplitterProcessorOutput, SplitterProcessorConfiguration]
):
    """
    Splitter processor
    """

    @staticmethod
    def name() -> str:
        return "Splitter"

    @staticmethod
    def slug() -> str:
        return "splitter"

    @staticmethod
    def description() -> str:
        return "Splits a string into smaller chunks based on the specified delimiter"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    def process(self) -> dict:
        output_stream = self._output_stream

        input_str = self._input.input_str
        splitter = self._config.splitter
        output_list = []

        if isinstance(splitter, CharacterSplitter):
            splitter = CharacterTextSplitter(
                chunk_size=splitter.chunk_size, chunk_overlap=splitter.chunk_overlap, separator=splitter.separator
            )
            output_list = splitter.split_text(input_str)
        elif isinstance(splitter, HTMLSplitter):
            splitter = HtmlSplitter(chunk_size=splitter.chunk_size)
            output_list = splitter.split_text(input_str)

        async_to_sync(output_stream.write)(
            SplitterProcessorOutput(output_list=output_list, output_str=json.dumps(output_list))
        )

        output = output_stream.finalize()
        return output
