import json
import logging
import random
from enum import Enum
from typing import List
from typing import Optional
from typing import Sequence
from typing import Union

import grpc
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from google.protobuf.json_format import MessageToJson
from PIL import Image
from pydantic import Field
from stability_sdk import client

from common.blocks.base.processor import BaseConfiguration
from common.blocks.base.processor import BaseInput
from common.blocks.base.processor import BaseInputEnvironment
from common.blocks.base.processor import BaseOutputType
from common.blocks.llm import LLMBaseProcessor
from common.blocks.base.processor import Schema

logger = logging.getLogger(__name__)


class Sampler(str, Enum):
    ddim = 'ddim'
    plms = 'plms'
    k_euler = 'k_euler'
    k_euler_ancestral = 'k_euler_ancestral'
    k_heun = 'k_heun'
    k_dpm_2 = 'k_dpm_2'
    k_dpm_2_ancestral = 'k_dpm_2_ancestral'
    k_dpmpp_2m = 'k_dpmpp_2m'

    def __str__(self):
        return self.value


class GuidancePreset(str, Enum):
    simple = 'simple'
    fast_blue = 'fast_blue'
    fast_green = 'fast_green'
    slow = 'slow'
    slower = 'slower'
    slowest = 'slowest'

    def __str__(self):
        return self.value


class StableDiffusionModel(str, Enum):
    STABLE_DIFFUSION_V1 = 'stable-diffusion-v1'
    STABLE_DIFFUSION_V1_5 = 'stable-diffusion-v1-5'
    STABLE_DIFFUSION_512_V2_0 = 'stable-diffusion-512-v2-0'
    STABLE_DIFFUSION_768_V2_0 = 'stable-diffusion-512-v2-0'
    STABLE_DIFFUSION_512_V2_1 = 'stable-diffusion-512-v2-1'
    STABLE_DIFFUSION_768_V2_1 = 'stable-diffusion-768-v2-1'

    def __str__(self):
        return self.value


def get_guidance_preset_enum(preset):
    if preset == None:
        return generation.GUIDANCE_PRESET_NONE

    return generation.GUIDANCE_PRESET_NONE


def get_sampler_grpc_enum(sampler):
    if sampler == None:
        return generation.SAMPLER_K_DPMPP_2M
    if sampler == 'ddim':
        return generation.SAMPLER_DDIM
    elif sampler == 'plms':
        return generation.SAMPLER_DDPM
    elif sampler == 'k_euler':
        return generation.SAMPLER_K_EULER
    elif sampler == 'k_euler_ancestral':
        return generation.SAMPLER_K_EULER_ANCESTRAL
    elif sampler == 'k_heun':
        return generation.SAMPLER_K_HEUN
    elif sampler == 'k_dpm_2':
        return generation.SAMPLER_K_DPM_2
    elif sampler == 'k_dpm_2_ancestral':
        return generation.SAMPLER_K_DPM_2_ANCESTRAL
    elif sampler == 'k_dpmpp_2s_ancestral':
        return generation.SAMPLER_K_DPMPP_2S_ANCESTRAL
    elif sampler == 'k_dpmpp_2m':
        return generation.SAMPLER_K_DPMPP_2M


class StabilityAIGrpcInputEnvironment(BaseInputEnvironment):
    stability_ai_api_key: str = Field(..., description='Stability AI API Key')
    user: Optional[str] = Field(default='', description='User')


class StabilityAIGrpcProcessorInput(BaseInput):
    env: Optional[StabilityAIGrpcInputEnvironment]


class StabilityAIGrpcProcessorOutput(BaseInput):
    pass


class StabilityAIGrpcProcessorConfiguration(BaseConfiguration):
    engine_id: StableDiffusionModel = Field(
        default=StableDiffusionModel.STABLE_DIFFUSION_V1_5, description='Inference engine (model) to use.',
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
        default=0, description='Seed for random latent noise generation. Deterministic if not being used in concert with CLIP Guidance. If not specified, or set to 0, then a random value will be used.',
    )

    num_samples: int = Field(
        default=1, description='Number of images to generate. Allows for batch image generations.',
    )

    guidance_preset: Optional[GuidancePreset] = Field(
        default=None,  widget='hidden', description='Guidance preset to use for image generation.',
    )


class StabilityAIGrpcProcessorOutputMetadata(Schema):
    raw_response: dict = Field(
        {}, description='The raw response from the API',
    )


class StabilityAIText2ImageGrpcProcessorInput(StabilityAIGrpcProcessorInput):
    prompt: List[str] = Field(
        default=[''], description='Text prompt to use for image generation.',
    )

    negative_prompt: List[str] = Field(
        default=[''], description='Negative text prompt to use for image generation.',
    )


class StabilityAIText2ImageGrpcProcessorOutput(StabilityAIGrpcProcessorOutput):
    metadata: Optional[StabilityAIGrpcProcessorOutputMetadata]
    answer: List[str] = Field(default=[], description='The generated images.')


def invoke_grpc_rpc(
    stability_ai_api_key: str,
    prompt: Union[str, List[str], generation.Prompt, List[generation.Prompt]],
    engine_id: StableDiffusionModel,
    init_image: Optional[Image.Image] = None,
    mask_image: Optional[Image.Image] = None,
    height: int = 512,
    width: int = 512,
    start_schedule: float = 1.0,
    end_schedule: float = 0.01,
    cfg_scale: float = 7.0,
    sampler: Sampler = None,
    steps: Optional[int] = None,
    seed: Union[Sequence[int], int] = 0,
    samples: int = 1,
    safety: bool = True,
    classifiers: Optional[generation.ClassifierParameters] = None,
    guidance_preset: GuidancePreset = GuidancePreset.simple,
    guidance_cuts: int = 0,
    guidance_strength: Optional[float] = None,
    guidance_prompt: Union[str, generation.Prompt] = None,
    guidance_models: List[str] = None,
):
    stability_api = client.StabilityInference(
        key=stability_ai_api_key,
        verbose=True,
        engine=engine_id,
    )
    try:
        grpc_response = stability_api.generate(
            prompt=prompt,
            height=height,
            width=width,
            cfg_scale=cfg_scale,
            sampler=get_sampler_grpc_enum(sampler),
            steps=steps,
            seed=seed,
            samples=samples,
            guidance_preset=get_guidance_preset_enum(guidance_preset),
        )
    except grpc.RpcError as grpc_ex:
        logger.exception(grpc_ex)
        raise Exception(grpc_ex.details())
    except Exception as ex:
        logger.exception(ex)
        raise Exception(ex)

    api_response = {'data': []}
    for resp in grpc_response:
        api_response['data'].append(json.loads(MessageToJson(resp)))
    return api_response


class StabilityAIText2ImageGrpcProcessor(LLMBaseProcessor[StabilityAIText2ImageGrpcProcessorInput, StabilityAIText2ImageGrpcProcessorOutput, StabilityAIGrpcProcessorConfiguration]):
    @staticmethod
    def name() -> str:
        return 'stability_ai_text2image'
    
    def _process(self, input: StabilityAIText2ImageGrpcProcessorInput, configuration: StabilityAIGrpcProcessorConfiguration) -> BaseOutputType:
        stability_ai_api_key = input.env.stability_ai_api_key
        prompts = []
        for p in input.prompt:
            if p:
                prompts.append(
                    generation.Prompt(
                    text=p, parameters=generation.PromptParameters(weight=1),
                    ),
                )

        for p in input.negative_prompt:
            if p:
                prompts.append(
                    generation.Prompt(
                    text=p, parameters=generation.PromptParameters(weight=-1),
                    ),
                )

        seed = random.randint(
            0, 2147483646,
        ) if configuration.seed == 0 else configuration.seed

        api_response = invoke_grpc_rpc(
            stability_ai_api_key=stability_ai_api_key,
            prompt=prompts,
            engine_id=configuration.engine_id,
            height=configuration.height,
            width=configuration.width,
            cfg_scale=configuration.cfg_scale,
            sampler=configuration.sampler,
            steps=configuration.steps,
            seed=seed,
            samples=configuration.num_samples,
            guidance_preset=configuration.guidance_preset,
        )

        processed_response = []
        for entry in api_response['data']:
            if 'artifacts' in entry:
                for image_data in entry['artifacts']:
                    if image_data['type'] == 'ARTIFACT_IMAGE':
                        processed_response.append(
                            {'b64_json-image': image_data['binary'], 'mime-type': image_data['mime']},
                        )

        result = []
        for entry in api_response['data']:
            if 'artifacts' in entry:
                for image_data in entry['artifacts']:
                    if image_data['type'] == 'ARTIFACT_IMAGE':
                        result.append(
                            'data:{};base64,{}'.format(
                            image_data['mime'], image_data['binary'],
                            ),
                        )

        response = StabilityAIText2ImageGrpcProcessorOutput(
            answer=result, metadata={'raw_response': api_response},
        )

        return response
