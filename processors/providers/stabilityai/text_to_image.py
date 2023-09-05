import json
import logging
import random
from enum import Enum
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import grpc
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from asgiref.sync import async_to_sync
from google.protobuf.json_format import MessageToJson
from pydantic import Field
from stability_sdk import client

from common.utils.utils import get_key_or_raise
from processors.providers.api_processor_interface import ApiProcessorInterface
from processors.providers.api_processor_interface import ApiProcessorSchema
from processors.providers.api_processor_interface import IMAGE_WIDGET_NAME
from processors.providers.stabilityai.utils import get_guidance_preset_enum
from processors.providers.stabilityai.utils import get_sampler_grpc_enum
from processors.providers.stabilityai.utils import GuidancePreset
from processors.providers.stabilityai.utils import Sampler


logger = logging.getLogger(__name__)


class StableDiffusionModel(str, Enum):
    STABLE_DIFFUSION_V1 = 'stable-diffusion-v1'
    STABLE_DIFFUSION_V1_5 = 'stable-diffusion-v1-5'
    STABLE_DIFFUSION_512_V2_0 = 'stable-diffusion-512-v2-0'
    STABLE_DIFFUSION_768_V2_0 = 'stable-diffusion-512-v2-0'
    STABLE_DIFFUSION_512_V2_1 = 'stable-diffusion-512-v2-1'
    STABLE_DIFFUSION_768_V2_1 = 'stable-diffusion-768-v2-1'
    STABLE_DIFFUSION_XL = 'stable-diffusion-xl-beta-v2-2-2'

    def __str__(self):
        return self.value


class TextToImageInput(ApiProcessorSchema):
    prompt: List[str] = Field(
        default=[''], description='Text prompt to use for image generation.',
    )

    negative_prompt: List[str] = Field(
        default=[''], description='Negative text prompt to use for image generation.',
    )


class TextToImageOutput(ApiProcessorSchema):
    answer: List[str] = Field(
        default=[], description='The generated images.', widget=IMAGE_WIDGET_NAME,
    )
    api_response: Optional[Dict] = Field(
        default=None, description='The raw response from the API.', widget='hidden',
    )


class TextToImageConfiguration(ApiProcessorSchema):
    engine_id: StableDiffusionModel = Field(
        default=StableDiffusionModel.STABLE_DIFFUSION_V1_5, description='Inference engine (model) to use.', advanced_parameter=False,
    )
    height: Optional[int] = Field(
        default=512, description='Measured in pixels. Pixel limit is 1048576',
    )
    width: Optional[int] = Field(
        default=512, description='Measured in pixels. Pixel limit is 1048576.',
    )

    cfg_scale: Optional[int] = Field(
        default=7, description='Dictates how closely the engine attempts to match a generation to the provided prompt. v2-x models respond well to lower CFG (4-8), where as v1-x models respond well to a higher range (IE: 7-14).',
    )

    sampler: Sampler = Field(
        default=Sampler.k_euler,
        description='Sampling engine to use. If no sampler is declared, an appropriate default sampler for the declared inference engine will be applied automatically.',
    )
    steps: Optional[int] = Field(
        default=30, description='Affects the number of diffusion steps performed on the requested generation.',
    )

    seed: Optional[int] = Field(
        default=0, description='Seed for random latent noise generation. Deterministic if not being used in concert with CLIP Guidance. If not specified, or set to 0, then a random value will be used.', advanced_parameter=False,
    )

    num_samples: int = Field(
        default=1, description='Number of images to generate. Allows for batch image generations.', advanced_parameter=True,
    )

    guidance_preset: Optional[GuidancePreset] = Field(
        default=None,  widget='hidden', description='Guidance preset to use for image generation.',
    )


class TextToImage(ApiProcessorInterface[TextToImageInput, TextToImageOutput, TextToImageConfiguration]):
    """
    StabilityAI Images Generations API
    """
    @staticmethod
    def name() -> str:
        return 'stability ai/text2image'

    @staticmethod
    def slug() -> str:
        return 'text2image'

    @staticmethod
    def provider_slug() -> str:
        return 'stabilityai'

    def process(self) -> dict:
        stability_api_key = get_key_or_raise(
            self._env, 'stabilityai_api_key', 'No stabilityai_api_key found in _env',
        )
        prompt = self._input.prompt
        if not prompt:
            raise Exception('Prompt is required')

        negative_prompt = self._input.negative_prompt
        prompts = []
        for p in prompt:
            if p:
                prompts.append(
                    generation.Prompt(
                        text=p, parameters=generation.PromptParameters(
                            weight=1),
                    ),
                )

        for p in negative_prompt:
            if p:
                prompts.append(
                    generation.Prompt(
                        text=p, parameters=generation.PromptParameters(
                            weight=-1),
                    ),
                )

        if self._config.seed == 0:
            self._config.seed = random.randint(0, 2147483646)

        stability_api = client.StabilityInference(
            key=stability_api_key,
            verbose=True,
            engine=self._config.engine_id,
        )
        try:
            grpc_response = stability_api.generate(
                prompt=prompts,
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
            )
        except grpc.RpcError as grpc_ex:
            logger.exception(grpc_ex)
            raise Exception(grpc_ex.details())
        except Exception as ex:
            logger.exception(ex)
            raise Exception(ex)

        api_response = {'data': []}
        image_count = 0
        for resp in grpc_response:
            resp_json = json.loads(MessageToJson(resp))
            api_response['data'].append(resp_json)
            if 'artifacts' in resp_json:
                for image_data in resp_json['artifacts']:
                    if image_data['type'] == 'ARTIFACT_IMAGE':
                        async_to_sync(self._output_stream.write)(
                            TextToImageOutput(
                                answer=(['' for _ in range(
                                    image_count)] + ['data:{};base64,{}'.format(image_data['mime'], image_data['binary'])]),
                            ),
                        )
                        image_count += 1

        async_to_sync(self._output_stream.write)(
            TextToImageOutput(answer=[''], api_response=api_response),
        )
        return self._output_stream.finalize()
