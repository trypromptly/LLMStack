from enum import Enum
from typing import Literal

from pydantic import BaseModel, field_validator


class Currrency(str, Enum):
    USD = "USD"


class BaseBillingMetric(BaseModel):
    identifier: str
    unit_cost: float
    currency: Currrency = Currrency.USD

    @field_validator("unit_cost")
    @classmethod
    def round_unit_cost(cls, v):
        return round(v, 6)

    def calculate_cost(self, **kwargs) -> int:
        raise NotImplementedError


class InvocationMetric(BaseBillingMetric):
    identifier: Literal["invocation"] = "invocation"

    def calculate_cost(self, **kwargs) -> float:
        return self.unit_cost * kwargs.get("invocation", 0)


DEFAULT_INVOCATION_PRICING = InvocationMetric(unit_cost=1000)

PRICES = {}


def get_pricing_data(provider_slug: str, processor_slug: str, model_slug: str, deployment_slug: str) -> dict:
    """
    Get pricing data for a given provider, processor, and model
    """
    return (
        PRICES.get(provider_slug, {})
        .get(processor_slug, {})
        .get(model_slug, {})
        .get(deployment_slug, {"pricing_metrics": {InvocationMetric.identifier: DEFAULT_INVOCATION_PRICING}})
    )
