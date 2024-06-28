from enum import Enum


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
