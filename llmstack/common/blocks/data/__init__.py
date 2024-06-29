from typing import Any, Dict, Optional

from llmstack.common.blocks.base.schema import BaseSchema


class DataDocument(BaseSchema):
    content: Optional[bytes] = None
    content_text: Optional[str] = None
    metadata: Dict[str, Any] = {}
