from typing import Optional

from pydantic import Field
from llmstack.common.blocks.base.schema import BaseSchema

class Oauth2BaseConfiguration(BaseSchema):
    connection_type_slug: str = Field(default='oauth2', widget='hidden')