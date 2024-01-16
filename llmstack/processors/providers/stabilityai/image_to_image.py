import json
import logging
from typing import Any, List, Optional

import grpc
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from google.protobuf.json_format import MessageToJson
from pydantic import Field
from stability_sdk import client

from llmstack.common.utils.utils import get_key_or_raise
from llmstack.processors.providers.api_processor_interface import (
    IMAGE_WIDGET_NAME, ApiProcessorInterface, ApiProcessorSchema)

from .utils import (GuidancePreset, Sampler, get_guidance_preset_enum,
                    get_sampler_grpc_enum)

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


class ImageToImageConfiguration(ApiProcessorSchema):
    engine_id: str = "stable-diffusion-512-v2-0"
    """
    Inference engine (model) to use.
    """
    height: Optional[int] = 512
    """
    Measured in pixels. Pixel limit is 1048576
    """
    width: Optional[int] = 512
    """
    Measured in pixels. Pixel limit is 1048576.
    """
    cfg_scale: Optional[int] = 7
    """
    Dictates how closely the engine attempts to match a generation to the provided prompt. v2-x models respond well to lower CFG (4-8), where as v1-x models respond well to a higher range (IE: 7-14).
    """
    sampler: Optional[Sampler] = Sampler.k_euler
    """
    Sampling engine to use. If no sampler is declared, an appropriate default sampler for the declared inference engine will be applied automatically.
    """
    steps: Optional[int] = None
    """
    Affects the number of diffusion steps performed on the requested generation.
    """
    seed: Optional[int] = None
    """
    Seed for random latent noise generation. Deterministic if not being used in concert with CLIP Guidance. If not specified, or set to 0, then a random value will be used.
    """
    num_samples: int = 1
    """
    Number of images to generate. Allows for batch image generations.
    """
    guidance_preset: Optional[GuidancePreset] = None
    """
    CLIP guidance preset, use with ancestral sampler for best results.
    """
    guidance_strength: Optional[float] = None
    """
    How strictly the diffusion process adheres to the prompt text (higher values keep your image closer to your prompt).
    """


class ImageToImageInput(ApiProcessorSchema):
    init_image: str
    prompt: str
    negative_prompt: Optional[str] = None


class ImageToImageOutput(ApiProcessorSchema):
    answer: List[str] = Field(
        default=[],
        description="The generated images.",
        widget=IMAGE_WIDGET_NAME,
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

    def process(self, input: dict) -> dict:
        _env = self._env
        stability_api_key = get_key_or_raise(
            _env,
            "stabilityai_api_key",
            "No stabilityai_api_key found in _env",
        )

        init_image = self._input.init_image
        prompt = self._input.prompt
        if not prompt or not init_image:
            raise Exception("Prompt and init_image are required")

        negative_prompt = self._input.negative_prompt
        prompts = []
        for p in prompt.split(","):
            if p:
                prompts.append(
                    generation.Prompt(
                        text=p,
                        parameters=generation.PromptParameters(
                            weight=1,
                        ),
                    ),
                )

        for p in negative_prompt.split(","):
            if p:
                prompts.append(
                    generation.Prompt(
                        text=p,
                        parameters=generation.PromptParameters(
                            weight=-1,
                        ),
                    ),
                )

        stability_api = client.StabilityInference(
            key=stability_api_key,
            verbose=True,
            engine=self._config.engine_id,
        )
        try:
            grpc_response = stability_api.generate(
                prompt=prompts,
                init_image=init_image,
                height=self._config.height,
                width=self._config.width,
                cfg_scale=self._config.cfg_scale,
                sampler=get_sampler_grpc_enum(self._config.sampler),
                steps=self._config.steps,
                seed=self._config.seed,
                samples=self._config.num_samples,
                guidance_preset=get_guidance_preset_enum(
                    self._config.guidance_preset,
                ),
                guidance_strength=self._config.guidance_strength,
            )
        except grpc.RpcError as grpc_ex:
            logger.exception(grpc_ex)
            raise Exception(grpc_ex.details())
        except Exception as ex:
            logger.exception(ex)
            raise Exception(ex)

        api_response = {"data": []}
        for resp in grpc_response:
            api_response["data"].append(json.loads(MessageToJson(resp)))

        result = []
        for entry in api_response["data"]:
            if "artifacts" in entry:
                for image_data in entry["artifacts"]:
                    if image_data["type"] == "ARTIFACT_IMAGE":
                        result.append(
                            "data:{};base64, {}".format(
                                image_data["mime"],
                                image_data["binary"],
                            ),
                        )

        response = ImageToImageOutput(answer=result)
        return response
