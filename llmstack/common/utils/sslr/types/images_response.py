# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from openai._models import BaseModel

from .image import Image

__all__ = ["ImagesResponse"]


class ImagesResponse(BaseModel):
    created: int

    data: List[Image]


class StabilityV1ImageResponse(BaseModel):
    artifacts: List[dict]
