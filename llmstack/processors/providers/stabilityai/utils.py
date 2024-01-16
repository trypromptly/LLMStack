from enum import Enum

import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation


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


def get_guidance_preset_enum(preset):
    if preset is None:
        return generation.GUIDANCE_PRESET_NONE

    return generation.GUIDANCE_PRESET_NONE


def get_sampler_grpc_enum(sampler):
    if sampler is None:
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
