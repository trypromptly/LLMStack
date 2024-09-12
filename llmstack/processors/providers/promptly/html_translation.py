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

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.blocks.base.schema import BaseSchema, StrEnum
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)
from llmstack.processors.providers.promptly import get_llm_client_from_provider_config
from llmstack.processors.providers.promptly.chat_completions import (
    OpenAIModelConfig,
    ProviderConfigType,
)

ELEMENT = namedtuple("Element", ["id", "element", "text"])
ELEMENT_WITH_ATTRIBUTE = namedtuple("ElementWithAttribute", ["id", "element", "attribute", "text"])

logger = logging.getLogger(__name__)


def has_non_text_nodes(element):
    return any(child for child in element.contents if child.name is not None)


class Language(StrEnum):
    ENGLISH = "English"
    GERMAN = "German"
    FRENCH = "French"
    SPANISH = "Spanish"
    PORTUGUESE = "Portuguese"


class HTMLTranslationInput(ApiProcessorSchema):
    html: str = Field(description="Input HTML to translate", json_schema_extra={"widget": "textarea"})
    input_language: Language = Field(description="Language to translate from", default=Language.ENGLISH)
    output_language: Language = Field(description="Language to translate to", default=Language.SPANISH)


class HTMLTranslationOutput(ApiProcessorSchema):
    translated_html: Optional[str] = Field(
        default=None, description="Translated HTML", json_schema_extra={"widget": "textarea"}
    )
    total_extracted_strings: Optional[int] = Field(default=0, description="Total extracted strings")
    total_translated_strings: Optional[int] = Field(default=0, description="Total translated strings")


class HTMLSelectorAttribute(BaseSchema):
    selector: str = Field(description="HTML selector")
    attribute: str = Field(description="HTML attribute")


class HTMLTranslationConfiguration(ApiProcessorSchema):
    system_message: str = Field(
        description="System message to use for LLM",
        default="You are a language translator. Translating text content from a HTML document. The text strings are provided as a JSON object with key-value pairs. The key is a unique identifier for the text provided in the value. Always reply a valid JSON object.",
        json_schema_extra={"widget": "textarea"},
    )
    translation_guideline: Optional[str] = Field(
        description="Instructions for the translations",
        default=None,
        json_schema_extra={"widget": "textarea"},
    )
    provider_config: ProviderConfigType = Field(description="Provider configuration", default=OpenAIModelConfig())

    chunk_size: int = Field(
        description="Chunk size for translation",
        default=1000,
        json_schema_extra={},
    )

    html_selectors: List[str] = Field(
        description="List of HTML selectors to translate",
        default=["p", "h1", "h2", "h3", "h4", "h5", "h6", "a", "span", "li", "td", "th", "caption", "label"],
    )

    html_selectors_attributes: List[HTMLSelectorAttribute] = Field(
        description="List of HTML selectors attributes to translate",
        default=[HTMLSelectorAttribute(selector="img", attribute="alt")],
    )
    max_parallel_requests: int = Field(
        description="Max parallel requests to make to the translation provider",
        default=4,
        le=10,
    )
    temperature: float = Field(
        description="The temperature of the random number generator.",
        default=0.7,
        le=1.0,
        ge=0.0,
    )
    seed: Optional[int] = Field(
        description="The seed used to generate the random number.",
        default=None,
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

    @classmethod
    def get_output_template(cls) -> OutputTemplate | None:
        return OutputTemplate(
            markdown="{{translated_html}}",
            jsonpath="$.translated_html",
        )

    def _translate_with_provider(self, chunk: str) -> str:
        json_input = json.loads(chunk)

        llm_client = get_llm_client_from_provider_config(
            str(self._config.provider_config.provider),
            self._config.provider_config.model.value,
            self.get_provider_config,
        )

        if llm_client is None:
            raise ValueError("LLM client not found")

        translation_prompt = (
            "You are provided a JSON list of strings to translate."
            + "Your task is to translate the text in the list. You will translate the text"
            + f" from {self._input.input_language} language to {self._input.output_language}"
            + " language. Always respond with a valid JSON list only. If you are not able to translate the text, return the same text. Make sure the returned JSON list has the same order and length as the input JSON list. Do not use ```json in the response."
        )

        if self._config.translation_guideline:
            translation_prompt += f"\nIn addition to the above instructions follow the following guidelines for translation {self._config.translation_guideline}"

        chunks_json = json.loads(chunk)
        final_chunks_json = {}
        final_chunks_set = set()
        for key, value in chunks_json.items():
            if value.strip() == "":
                # Skip empty strings
                continue
            if value in self._translation_mapping or value in final_chunks_set:
                continue

            final_chunks_json[key] = value
            final_chunks_set.add(value)

        translation_prompt += f"\n---\n{json.dumps(list(final_chunks_json.values()))}"

        messages = [
            {"role": "system", "content": self._config.system_message},
            {"role": "user", "content": translation_prompt},
        ]

        response = llm_client.chat.completions.create(
            messages=messages,
            model=self._config.provider_config.model.value,
            temperature=self._config.temperature,
            stream=True,
            seed=self._config.seed,
            n=1,
        )
        model_response = ""

        for result in response:
            model_response += result.choices[0].delta.content_str

        json_result = {}
        try:
            json_result = json.loads(model_response)
        except Exception as e:
            logger.error(f"Error: {e}, response: {model_response}")

        output_json = {}
        for index, entry in enumerate(final_chunks_json.keys()):
            output_json[entry] = json_result[index]
            self._translation_mapping[final_chunks_json[entry]] = json_result[index]

        for index, entry in enumerate(json_input.keys()):
            if json_input[entry] in self._translation_mapping:
                output_json[entry] = self._translation_mapping[json_input[entry]]
            elif entry not in output_json:
                output_json[entry] = json_input[entry]

        return output_json

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
        seen_values = set()
        for key, value in element_text_dict.items():
            if value not in seen_values:
                entry_length = len(value)
                seen_values.add(value)
            else:
                entry_length = 0

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
        self._translation_mapping = {}

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
