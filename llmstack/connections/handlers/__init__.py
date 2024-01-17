from typing import Optional

from llmstack.common.blocks.base.schema import BaseSchema


class Oauth2BaseConfiguration(BaseSchema):
    token: Optional[str]
