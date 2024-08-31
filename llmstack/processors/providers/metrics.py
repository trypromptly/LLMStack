from enum import IntEnum


class MetricType(IntEnum):
    INVOCATION = 1
    INPUT_TOKENS = 2
    OUTPUT_TOKENS = 3
    RESOLUTION = 4
    API_INVOCATION = 5
