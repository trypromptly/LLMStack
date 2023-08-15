from typing import Any, Dict, Optional
from common.blocks.base.schema import BaseSchema

class DataDocument(BaseSchema):
    content:Optional[bytes]
    content_text: Optional[str]
    metadata: Dict[str, Any] = {}