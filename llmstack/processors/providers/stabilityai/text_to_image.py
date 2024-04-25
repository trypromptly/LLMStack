import logging
from enum import Enum
from typing import List, Optional

from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class StabilityAIModel(str, Enum):
    STABLE_DIFFUSION_XL = "stable-diffusion-xl"
    STABLE_DIFFUSION = "stable-diffusion"
    STABLE_DIFFUSION_XL_BETA = "stable-diffusion-xl-beta"
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
        elif self.value == "stable-diffusion-xl-beta":
            return "stable-diffusion-xl-beta-v2-2-2"
        elif self.value == "core":
            return "core"
        elif self.value == "sd3":
            return "sd3"
        elif self.value == "sd3-turbo":
            return "sd3-turbo"
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


class TextToImageInput(ApiProcessorSchema):
    prompt: List[str] = Field(
        default=[""],
        description="Text prompt to use for image generation.",
    )

    negative_prompt: List[str] = Field(
        default=[""],
        description="Negative text prompt to use for image generation.",
    )


class TextToImageOutput(ApiProcessorSchema):
    answer: List[str] = Field(
        default=[],
        description="The generated images.",
    )


class TextToImageConfiguration(ApiProcessorSchema):
    engine_id: StabilityAIModel = Field(
        default=StabilityAIModel.STABLE_DIFFUSION_XL,
        description="Inference engine (model) to use.",
        advanced_parameter=False,
    )
    height: Optional[int] = Field(
        default=512,
        description="Measured in pixels. Pixel limit is 1048576",
    )
    width: Optional[int] = Field(
        default=512,
        description="Measured in pixels. Pixel limit is 1048576.",
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
        advanced_parameter=False,
    )

    num_samples: int = Field(
        default=1,
        description="Number of images to generate. Allows for batch image generations.",
        advanced_parameter=True,
    )

    guidance_preset: Optional[GuidancePreset] = Field(
        default=None,
        widget="hidden",
        description="Guidance preset to use for image generation.",
    )


class TextToImage(ApiProcessorInterface[TextToImageInput, TextToImageOutput, TextToImageConfiguration]):
    """
    StabilityAI Images Generations API
    """

    @staticmethod
    def name() -> str:
        return "Text2Image"

    @staticmethod
    def slug() -> str:
        return "text2image"

    @staticmethod
    def description() -> str:
        return "Generates images from a series of prompts and negative prompts"

    @staticmethod
    def provider_slug() -> str:
        return "stabilityai"

    @classmethod
    def get_output_template(cls) -> Optional[OutputTemplate]:
        return OutputTemplate(
            markdown="""{{ for image in answer }}![Generated Image]({{ image }}){{ endfor }}""",
        )

    def process(self) -> dict:
        from llmstack.common.utils.sslr import LLM

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
        object_ref = self._upload_asset_from_url(asset=data_uri)
        async_to_sync(self._output_stream.write)(
            TextToImageOutput(answer=[object_ref]),
        )
        output = self._output_stream.finalize()
        return output
