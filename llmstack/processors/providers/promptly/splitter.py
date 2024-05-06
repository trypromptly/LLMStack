import io
import json
import logging
import uuid
from enum import Enum
from typing import List, Literal, Optional, Union

from asgiref.sync import async_to_sync
from pydantic import Field
from unstructured.partition.auto import partition

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.blocks.base.schema import BaseSchema as Schema
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.promptly.file_operations import FileMimeType

logger = logging.getLogger(__name__)


class SplitterProcessorInput(ApiProcessorSchema):
    content: Optional[str] = Field(
        default="",
        description="The contents of the file. Skip this field if you want to create an archive of the directory",
        widget="textarea",
    )
    content_uri: Optional[str] = Field(
        default=None,
        description="The URI of the content to be used to as file",
    )
    content_mime_type: Optional[FileMimeType] = Field(
        default=FileMimeType.TEXT,
        description="The mimetype of the content.",
    )
    content_objref: Optional[str] = Field(
        default=None,
        description="Object ref of the content to be used to create the file",
    )


class SplitterProcessorOutput(ApiProcessorSchema):
    outputs: List[str] = []
    objrefs: List[str] = []
    outputs_text: str = ""


class SplitterMode(str, Enum):
    TEXT = "text"
    URI = "uri"
    OBJREF = "objref"

    def __str__(self):
        return self.value


class NoStrategy(Schema):
    type: Literal["NoStrategy"] = "NoStrategy"


class BasicStartegy(Schema):
    type: Literal["BasicStrategy"] = "BasicStrategy"
    max_characters: Optional[int] = Field(default=2000, title="Max Characters", description="Max characters")
    new_after_n_chars: Optional[int] = Field(
        default=2000,
        title="New After N Chars",
        description="Cuts off chunks once they reach a length of n characters; a soft max.",
    )
    overlap: Optional[int] = Field(
        default=100,
        title="Overlap",
        description="Specifies the length of a string ('tail') to be drawn from each chunk and prefixed to the next chunk as a context-preserving mechanism. By default, this only applies to split-chunks where an oversized element is divided into multiple chunks by text-splitting.",
    )
    overlap_all: Optional[bool] = Field(
        default=False,
        title="Overlap All",
        description="When True, apply overlap between 'normal' chunks formed from whole elements and not subject to text-splitting. Use this with caution as it produces a certain level of 'pollution' of otherwise clean semantic chunk boundaries.",
    )


class ByTitleStartegy(Schema):
    type: Literal["ByTitleStrategy"] = "ByTitleStrategy"
    max_characters: Optional[int] = Field(default=2000, title="Max Characters", description="Max characters")
    multipage_sections: Optional[bool] = Field(
        default=True,
        title="Multipage Sections",
        description="If True, sections can span multiple pages.",
    )
    combine_text_under_n_chars: Optional[int] = Field(
        default=2000,
        title="Combine Text Under N Chars",
        description="Combines elements (for example a series of titles) until a section reaches a length of n characters. Only applies to 'by_title' strategy.",
    )
    new_after_n_chars: Optional[int] = Field(
        default=2000,
        title="New After N Chars",
        description="Cuts off chunks once they reach a length of n characters; a soft max.",
    )
    max_characters: Optional[int] = Field(
        default=2000,
        title="Max Characters",
        description="Chunks elements text and text_as_html (if present) into chunks of length n characters, a hard max.",
    )


class SplitterProcessorConfiguration(ApiProcessorSchema):
    objref: Optional[bool] = Field(
        default=False,
        title="Output as Object Reference",
        description="Return output as object reference instead of raw text.",
        advanced_parameter=True,
    )
    mode: SplitterMode = Field(
        default=SplitterMode.TEXT,
        title="Output Mode",
        description="Output mode",
        advanced_parameter=True,
    )
    merge_strategy: Optional[Union[NoStrategy, BasicStartegy, ByTitleStartegy]] = Field(
        default=None,
        descriminator="type",
        title="Merge Strategy",
        description="Merge strategy",
        advanced_parameter=True,
    )


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

    @classmethod
    def get_output_template(cls) -> OutputTemplate | None:
        markdown_template = """{{outputs_text}}"""
        return OutputTemplate(markdown=markdown_template)

    def process(self) -> dict:
        input_content_bytes = None
        input_content_mime_type = None
        input_filename = f"{str(uuid.uuid4())}"
        chunks = []
        data_uri = None

        output_stream = self._output_stream

        if self._input.content:
            input_content_bytes = self._input.content.encode("utf-8")
            input_content_mime_type = self._input.content_mime_type or FileMimeType.TEXT

        if self._input.content_uri:
            if self._input.content_uri.startswith("data:"):
                data_uri = self._input.content_uri
                input_content_mime_type, _, input_content_bytes = validate_parse_data_uri(data_uri)
            else:
                raise ValueError("Only data URI is supported for content URI")

        if self._input.content_objref:
            # Get the content from the object ref
            file_data_url = self._get_session_asset_data_uri(self._input.content_objref, include_name=True)
            input_content_mime_type, _, input_content_bytes = validate_parse_data_uri(file_data_url)

        file = io.BytesIO(input_content_bytes)
        partitions = partition(content_type=input_content_mime_type, file=file, file_filename=input_filename)

        if self._config.merge_strategy:
            logger.info(f"Merge strategy: {self._config.merge_strategy}")
            logger.info(f"Type: {type(self._config.merge_strategy)}")
            # Merge the partitions based on the merge strategy
            if isinstance(self._config.merge_strategy, BasicStartegy):
                logger.info("Basic strategy")
                from unstructured.chunking.basic import chunk_elements

                partitions = chunk_elements(
                    partitions,
                    max_characters=self._config.merge_strategy.max_characters,
                    new_after_n_chars=self._config.merge_strategy.new_after_n_chars,
                    overlap=self._config.merge_strategy.overlap,
                    overlap_all=self._config.merge_strategy.overlap_all,
                )
            elif isinstance(self._config.merge_strategy, ByTitleStartegy):
                logger.info("By Title strategy")
                from unstructured.chunking.title import chunk_by_title

                partitions = chunk_by_title(
                    partitions,
                    combine_text_under_n_chars=self._config.merge_strategy.combine_text_under_n_chars,
                    max_characters=self._config.merge_strategy.max_characters,
                    multipage_sections=self._config.merge_strategy.multipage_sections,
                    new_after_n_chars=self._config.merge_strategy.new_after_n_chars,
                )
        chunks = list(map(lambda x: x.text, partitions))

        async_to_sync(output_stream.write)(SplitterProcessorOutput(outputs=chunks, outputs_text=json.dumps(chunks)))
        output = output_stream.finalize()
        return output
