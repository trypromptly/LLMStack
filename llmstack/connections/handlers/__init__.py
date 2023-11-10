from typing import Optional
from llmstack.common.blocks.base.schema import BaseSchema

class Oauth2BaseConfiguration(BaseSchema):
    connection_type_slug: Optional[str]