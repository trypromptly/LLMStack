from llmstack.common.blocks.base.schema import StrEnum


class Sampler(StrEnum):
    ddim = "ddim"
    plms = "plms"
    k_euler = "k_euler"
    k_euler_ancestral = "k_euler_ancestral"
    k_heun = "k_heun"
    k_dpm_2 = "k_dpm_2"
    k_dpm_2_ancestral = "k_dpm_2_ancestral"
    k_dpmpp_2m = "k_dpmpp_2m"


class GuidancePreset(StrEnum):
    simple = "simple"
    fast_blue = "fast_blue"
    fast_green = "fast_green"
    slow = "slow"
    slower = "slower"
    slowest = "slowest"
