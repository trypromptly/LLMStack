from typing import Optional

from llmstack.common.blocks.base.schema import BaseSchema


class Oauth2BaseConfiguration(BaseSchema):
    token: Optional[str] = None
    token_type: Optional[str] = None
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
