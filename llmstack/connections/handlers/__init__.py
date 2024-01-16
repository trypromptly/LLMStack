from typing import Optional

from pydantic import Field
from llmstack.common.blocks.base.schema import BaseSchema


class Oauth2BaseConfiguration(BaseSchema):
    token: Optional[str]
