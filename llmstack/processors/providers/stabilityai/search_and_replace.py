import base64
import logging
from enum import Enum
from typing import Optional

from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.utils.sslr.constants import PROVIDER_STABILITYAI
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class StabilityAIModel(str, Enum):
    CORE = "core"

    def __str__(self) -> str:
        return self.value

    def model_name(self):
        if self.value == "core":
            return "core"
        else:
            raise ValueError(f"Unknown model {self.value}")


class SearchAndReplaceProcessorInput(ApiProcessorSchema):
    image_file: Optional[str] = Field(
        default="",
        description="The file to extract text from",
        accepts={
            "image/jpeg": [],
            "image/png": [],
        },
        maxSize=9000000,
        widget="file",
    )
    image_file_data: Optional[str] = Field(
        default="",
        description="The base64 encoded data of file",
        pattern=r"data:(.*);name=(.*);base64,(.*)",
    )

    prompt: str = Field(
        description="The prompt to use for image generation.",
    )

    search_prompt: str = Field(
        description="Text prompt to use for object search.",
    )

    negative_prompt: Optional[str] = Field(
        description="Negative text prompt to use for image generation.",
    )


class SearchAndReplaceProcessorOutput(ApiProcessorSchema):
    image: str = Field(
        default=[],
        description="The generated images.",
    )


class SearchAndReplaceProcessorConfiguration(ApiProcessorSchema):
    engine_id: StabilityAIModel = Field(
        default=StabilityAIModel.CORE,
        description="The model to use for the generation.",
    )

    seed: Optional[int] = Field(
        default=0,
        description="A specific value that is used to guide the 'randomness' of the generation.",
    )


class SearchAndReplaceProcessor(
    ApiProcessorInterface[
        SearchAndReplaceProcessorInput, SearchAndReplaceProcessorOutput, SearchAndReplaceProcessorConfiguration
    ]
):
    """
    StabilityAI Search and Replace API
    """

    @staticmethod
    def name() -> str:
        return "Search And Replace"

    @staticmethod
    def slug() -> str:
        return "search_and_replace"

    @staticmethod
    def description() -> str:
        return "Users can use a search_prompt to identify an object in simple language to be replaced."

    @staticmethod
    def provider_slug() -> str:
        return "stabilityai"

    @classmethod
    def get_output_template(cls) -> Optional[OutputTemplate]:
        return OutputTemplate(
            markdown="""![Generated Image]({{ image }})""",
        )

    def process(self) -> dict:
        from llmstack.common.utils.sslr import LLM
        from llmstack.common.utils.sslr._utils import resize_image_file

        image_file = self._input.image_file or None
        if (image_file is None or image_file == "") and self._input.image_file_data:
            image_file = self._input.image_file_data
        if image_file is None:
            raise Exception("No file found in input")

        # Extract from objref if it is one
        image_file = self._get_session_asset_data_uri(image_file)

        mime_type, file_name, data = validate_parse_data_uri(image_file)
        data_bytes = base64.b64decode(data)
        data_bytes = resize_image_file(data_bytes, max_pixels=9437184, max_size=10485760)

        client = LLM(provider=PROVIDER_STABILITYAI, stabilityai_api_key=self._env.get("stabilityai_api_key"))

        result = client.images.edit(
            prompt=" ".join(self._input.prompt),
            image=data_bytes,
            model=self._config.engine_id.model_name(),
            n=1,
            response_format="b64_json",
            operation="search_replace",
            extra_body={
                "search_prompt": self._input.search_prompt,
                "seed": self._config.seed,
                "negative_prompt": self._input.negative_prompt,
            },
        )
        image = result.data[0]
        data_uri = image.data_uri(include_name=True)
        object_ref = self._upload_asset_from_url(asset=data_uri)
        async_to_sync(self._output_stream.write)(
            SearchAndReplaceProcessorOutput(image=object_ref),
        )
        output = self._output_stream.finalize()
        return output
