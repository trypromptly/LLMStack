import concurrent.futures
import json
import logging
import uuid
from collections import namedtuple
from typing import List, Optional

from asgiref.sync import async_to_sync
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from pydantic import Field

from llmstack.common.blocks.base.schema import BaseSchema
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

ELEMENT = namedtuple("Element", ["id", "element", "text"])
ELEMENT_WITH_ATTRIBUTE = namedtuple("ElementWithAttribute", ["id", "element", "attribute", "text"])

logger = logging.getLogger(__name__)


def has_non_text_nodes(element):
    return any(child for child in element.contents if child.name is not None)


class HTMLTranslationInput(ApiProcessorSchema):
    html: str = Field(description="Input HTML to translate", widget="textarea")
    instructions: str = Field(
        description="Instructions for the translations",
        default="The output should be a JSON list without any code blocks. Translate the English content below between 2 lines of 0CigC9JQ9VLKOSYDkAfJVEnPv to German, and follow the guidelines below.",
        advanced_parameter=True,
        widget="textarea",
    )


class HTMLTranslationOutput(ApiProcessorSchema):
    translated_html: Optional[str] = Field(description="Translated HTML", widget="textarea")
    total_extracted_strings: Optional[int] = Field(description="Total extracted strings")
    total_translated_strings: Optional[int] = Field(description="Total translated strings")


class HTMLSelectorAttribute(BaseSchema):
    selector: str = Field(description="HTML selector")
    attribute: str = Field(description="HTML attribute")


class HTMLTranslationConfiguration(ApiProcessorSchema):
    system_message: str = Field(
        description="System message to use for LLM", default="You are a language translator.", advanced_parameter=False
    )

    chunk_size: int = Field(description="Chunk size for translation", default=1000, advanced_parameter=False)

    html_selectors: List[str] = Field(
        description="List of HTML selectors to translate",
        default=["p", "h1", "h2", "h3", "h4", "h5", "h6", "a", "span", "li", "td", "th", "caption", "label"],
    )

    html_selectors_attributes: List[HTMLSelectorAttribute] = Field(
        description="List of HTML selectors attributes to translate",
        default=[HTMLSelectorAttribute(selector="img", attribute="alt")],
    )
    placeholder_variable: str = Field(
        description="Placeholder variable to replace in the processed text",
        default="<CHUNK_PLACEHOLDER>",
        advanced_parameter=True,
    )
    max_parallel_requests: int = Field(
        description="Max parallel requests to make to the translation provider",
        default=4,
        advanced_parameter=True,
        le=10,
    )


class HTMLTranslationProcessor(
    ApiProcessorInterface[HTMLTranslationInput, HTMLTranslationOutput, HTMLTranslationConfiguration],
):
    """
    HTML Translation processor
    """

    @staticmethod
    def name() -> str:
        return "HTML Translation"

    @staticmethod
    def slug() -> str:
        return "html-translation"

    @staticmethod
    def description() -> str:
        return "Translate HTML"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    def _translate_with_provider(self, chunk: str) -> str:
        try:
            from openai import OpenAI

            json_input = json.loads(chunk)

            openai_client = OpenAI(api_key=self._env["openai_api_key"])
            system_message = {
                "role": "system",
                "content": self._config.system_message,
            }

            if self._config.placeholder_variable in self._input.instructions:
                message = f"{self._input.instructions.replace(self._config.placeholder_variable, chunk)}"
            else:
                message = f"{self._input.instructions}{chunk}"

            result = openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[system_message] + [{"role": "user", "content": message}],
                temperature=0.5,
                stream=False,
                seed=10,
                max_tokens=3000,
                response_format={"type": "json_object"},
            )

            json_result = json.loads(result.choices[0].message.content)

            for entry in json_input:
                if entry not in json_result:
                    json_result[entry] = json_input[entry]
            return json_result
        except Exception as e:
            logger.error(f"Error: {e}")
            return {}

    def _get_elements_with_text(self, html_element: BeautifulSoup) -> List[str]:
        if html_element.name is None:
            return [ELEMENT(uuid.uuid4(), html_element, html_element.text)]

        result = []
        for child in html_element.children:
            result.extend(self._get_elements_with_text(child))
        return result

    # Split a dict of uuid, text in to smaller dicts such that length of text of key and value is less than 5000
    def _split_element_text_dict(self, element_text_dict: dict) -> List[dict]:
        result = []
        current_dict = {}
        current_length = 0
        for key, value in element_text_dict.items():
            entry_length = len(value) + len(key)
            if current_dict and current_length + entry_length > self._config.chunk_size:
                result.append(current_dict)
                current_dict = {}
                current_length = 0

            current_dict[key] = value
            current_length += entry_length

        if current_dict:
            result.append(current_dict)

        return result

    def process(self) -> dict:
        total_extracted_strings = 0
        total_translated_strings = 0
        output_stream = self._output_stream
        html_input = self._input.html

        html_doc = BeautifulSoup(html_input, "html.parser")

        # Translate selector text

        selector_elements = []
        for selector in self._config.html_selectors:
            tag_elements = html_doc.select(selector)
            for tag_element in tag_elements:
                selector_elements.extend(self._get_elements_with_text(tag_element))

        orignal_text = dict((str(element.id), element.text) for element in selector_elements)
        nodes = dict((str(element.id), element) for element in selector_elements)
        processed_text = {}
        total_extracted_strings += len(orignal_text)

        async_to_sync(output_stream.write)(
            HTMLTranslationOutput(total_extracted_strings=total_extracted_strings),
        )

        orignal_text_chunks = self._split_element_text_dict(orignal_text)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self._config.max_parallel_requests) as executor:
            futures = [
                executor.submit(self._translate_with_provider, json.dumps(chunk)) for chunk in orignal_text_chunks
            ]

            for future_result in concurrent.futures.as_completed(futures):
                try:
                    total_translated_strings += len(future_result.result())
                    async_to_sync(output_stream.write)(
                        HTMLTranslationOutput(total_translated_strings=total_translated_strings),
                    )
                    for key, value in future_result.result().items():
                        processed_text[key] = value
                except Exception as e:
                    logger.error(f"Error: {e}")

        for id, value in processed_text.items():
            if id in nodes:
                if nodes[id].element.parent and len(nodes[id].element.parent.contents) == 1:
                    nodes[id].element.parent.string = value
                elif nodes[id].element.parent and len(nodes[id].element.parent.contents) > 1:
                    for content in nodes[id].element.parent.contents:
                        if content.string == orignal_text[id]:
                            content.replace_with(NavigableString(value))

                else:
                    nodes[id].element.string = value

        #  Translate attributes

        selector_elements_with_attribute_text = []
        for selector in self._config.html_selectors_attributes:
            tag_elements = html_doc.select(selector.selector)
            for tag_element in tag_elements:
                if tag_element.has_attr(selector.attribute):
                    selector_elements_with_attribute_text.append(
                        ELEMENT_WITH_ATTRIBUTE(
                            uuid.uuid4(),
                            tag_element,
                            selector.attribute,
                            tag_element[selector.attribute],
                        )
                    )

        orignal_text = dict((str(element.id), element.text) for element in selector_elements_with_attribute_text)
        nodes = dict((str(element.id), element) for element in selector_elements_with_attribute_text)
        processed_text = {}
        total_extracted_strings += len(orignal_text)

        async_to_sync(output_stream.write)(
            HTMLTranslationOutput(total_extracted_strings=total_extracted_strings),
        )

        orignal_text_chunks = self._split_element_text_dict(orignal_text)
        with concurrent.futures.ThreadPoolExecutor(max_workers=self._config.max_parallel_requests) as executor:
            futures = [
                executor.submit(self._translate_with_provider, json.dumps(chunk)) for chunk in orignal_text_chunks
            ]

            for future_result in concurrent.futures.as_completed(futures):
                try:
                    total_translated_strings += len(future_result.result())
                    async_to_sync(output_stream.write)(
                        HTMLTranslationOutput(total_translated_strings=total_translated_strings),
                    )
                    for key, value in future_result.result().items():
                        processed_text[key] = value
                except Exception as e:
                    logger.error(f"Error: {e}")

        for id, value in processed_text.items():
            if id in nodes:
                nodes[id].element[nodes[id].attribute] = value

        processed_html = str(html_doc)

        async_to_sync(output_stream.write)(
            HTMLTranslationOutput(translated_html=processed_html),
        )

        output = output_stream.finalize()
        return output
