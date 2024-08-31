from enum import Enum


class MetricType(Enum):
    INVOCATION = 1
    INPUT_TOKENS = 2
    OUTPUT_TOKENS = 3
    RESOLUTION = 4
    API_INVOCATION = 5

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self.value)

    @classmethod
    def from_int(cls, value):
        if isinstance(value, str):
            value = int(value)
        for metric in cls:
            if metric.value == value:
                return metric
        return None
