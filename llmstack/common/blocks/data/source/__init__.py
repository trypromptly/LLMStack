from typing import List, Optional

from llmstack.common.blocks.base.schema import BaseSchema
from llmstack.common.blocks.data import DataDocument


class DataSourceEnvironmentSchema(BaseSchema):
    openai_key: Optional[str] = None


class DataSourceInputSchema(BaseSchema):
    env: Optional[DataSourceEnvironmentSchema] = None


class DataSourceConfigurationSchema(BaseSchema):
    pass


class DataSourceOutputSchema(BaseSchema):
    documents: List[DataDocument]
