import logging
from enum import Enum
from typing import List, Optional

from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class StabilityAIModel(str, Enum):
    STABLE_DIFFUSION_XL = "stable-diffusion-xl"
    STABLE_DIFFUSION = "stable-diffusion"
    ESRGAN_V1 = "esrgan-v1"
    CORE = "core"
    SD_3 = "sd3"
    SD_3_TURBO = "sd3-turbo"

    def __str__(self) -> str:
        return self.value

    def model_name(self):
        if self.value == "stable-diffusion-xl":
            return "stable-diffusion-xl-1024-v1-0"
        elif self.value == "stable-diffusion":
            return "stable-diffusion-v1-6"
        elif self.value == "core":
            return "core"
        elif self.value == "sd3":
            return "sd3"
        elif self.value == "sd3-turbo":
            return "sd3-turbo"
        elif self.value == "esrgan-v1":
            return "esrgan-v1-x2plus"
        else:
            raise ValueError(f"Unknown model {self.value}")


class Sampler(str, Enum):
    ddim = "ddim"
    plms = "plms"
    k_euler = "k_euler"
    k_euler_ancestral = "k_euler_ancestral"
    k_heun = "k_heun"
    k_dpm_2 = "k_dpm_2"
    k_dpm_2_ancestral = "k_dpm_2_ancestral"
    k_dpmpp_2m = "k_dpmpp_2m"

    def __str__(self):
        return self.value


class GuidancePreset(str, Enum):
    simple = "simple"
    fast_blue = "fast_blue"
    fast_green = "fast_green"
    slow = "slow"
    slower = "slower"
    slowest = "slowest"

    def __str__(self):
        return self.value


class StylePreset(str, Enum):
    THREE_D = "3d-model"
    ANALOG_FILM = "analog-film"
    ANIME = "anime"
    CINEMATIC = "cinematic"
    COMIC_BOOK = "comic-book"
    DIGITAL_ART = "digital-art"
    ENHANCE = "enhance"
    FANTASY_ART = "fantasy-art"
    ISOMETRIC = "isometric"
    LINE_ART = "line-art"
    LOW_POLY = "low-poly"
    MODELING_COMPOUND = "modeling-compound"
    NEON_PUNK = "neon-punk"
    ORIGAMI = "origami"
    PHOTOGRAPHIC = "photographic"
    PIXEL_ART = "pixel-art"
    TILE_TEXTURE = "tile-texture"


class ImageToImageConfiguration(ApiProcessorSchema):
    engine_id: StabilityAIModel = Field(
        default=StabilityAIModel.STABLE_DIFFUSION_XL,
        description="Inference engine (model) to use.",
        json_schema_extra={"advanced_parameter": False},
    )
    height: Optional[int] = Field(
        default=512,
        description="Measured in pixels. Pixel limit is 1048576",
    )
    width: Optional[int] = Field(
        default=512,
        description="Measured in pixels. Pixel limit is 1048576.",
    )
    init_image_mode: Optional[str] = Field(
        default="image_strength",
        description="Whether to use image_strength or step_schedule_* to control how much influence the init_image has on the result.",
    )
    image_strength: Optional[float] = Field(
        default=0.35,
        multiple_of=0.01,
        description="How much influence the init_image has on the diffusion process. Values close to 1 will yield images very similar to the init_image while values close to 0 will yield images wildly different than the init_image.",
        json_schema_extra={"lte": 1.0, "gte": 0.0},
    )
    cfg_scale: Optional[int] = Field(
        default=7,
        description="Dictates how closely the engine attempts to match a generation to the provided prompt. v2-x models respond well to lower CFG (4-8), where as v1-x models respond well to a higher range (IE: 7-14).",
    )
    sampler: Sampler = Field(
        default=Sampler.k_euler,
        description="Sampling engine to use. If no sampler is declared, an appropriate default sampler for the declared inference engine will be applied automatically.",
    )
    steps: Optional[int] = Field(
        default=30,
        description="Affects the number of diffusion steps performed on the requested generation.",
    )
    seed: Optional[int] = Field(
        default=0,
        description="Seed for random latent noise generation. Deterministic if not being used in concert with CLIP Guidance. If not specified, or set to 0, then a random value will be used.",
        json_schema_extra={"advanced_parameter": False},
    )
    num_samples: int = Field(
        default=1,
        description="Number of images to generate. Allows for batch image generations.",
    )
    guidance_preset: Optional[GuidancePreset] = Field(
        default=None,
        description="Guidance preset to use for image generation.",
        json_schema_extra={"widget": "hidden"},
    )


class ImageToImageInput(ApiProcessorSchema):
    image_file: Optional[str] = Field(
        default="",
        description="The file to extract text from",
        json_schema_extra={"widget": "file", "accepts": {"image/*": []}, "maxSize": 50000000},
    )
    image_file_data: Optional[str] = Field(
        default="",
        description="The base64 encoded data of file",
    )

    prompt: List[str] = Field(
        default=[""],
        description="Text prompt to use for image generation.",
    )
    negative_prompt: List[str] = Field(
        default=[],
        description="Negative text prompt to use for image generation.",
    )
    style_preset: Optional[StylePreset] = Field(
        default=None,
        description="Pass in a style preset to guide the image model towards a particular style. This list of style presets is subject to change.",
    )


class ImageToImageOutput(ApiProcessorSchema):
    image: str = Field(
        description="The generated image.",
    )


class ImageToImage(
    ApiProcessorInterface[ImageToImageInput, ImageToImageOutput, ImageToImageConfiguration],
):
    """
    StabilityAI Images Generations API
    """

    @staticmethod
    def name() -> str:
        return "Image2Image"

    @staticmethod
    def slug() -> str:
        return "image2image"

    @staticmethod
    def description() -> str:
        return "Generates images from images"

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

        image_file = self._input.image_file or None
        if (image_file is None or image_file == "") and self._input.image_file_data:
            image_file = self._input.image_file_data
        if image_file is None:
            raise Exception("No file found in input")

        # Extract from objref if it is one
        image_file = self._get_session_asset_data_uri(image_file)

        mime_type, file_name, data = validate_parse_data_uri(image_file)

        client = LLM(
            provider="stabilityai",
            stabilityai_api_key=self._env.get("stabilityai_api_key"),
        )
        result = client.images.generate(
            prompt=" ".join(self._input.prompt),
            negative_prompt=" ".join(self._input.negative_prompt) if self._input.negative_prompt else None,
            model=self._config.engine_id.model_name(),
            n=1,
            response_format="b64_json",
            size=f"{self._config.width}x{self._config.height}",
        )
        image = result.data[0]
        data_uri = image.data_uri(include_name=True)
        objref = self._upload_asset_from_url(asset=data_uri).objref
        async_to_sync(self._output_stream.write)(
            ImageToImageOutput(image=objref),
        )
        output = self._output_stream.finalize()
        return output
