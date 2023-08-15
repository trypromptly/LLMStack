from pydantic import AnyUrl
from typing import List, Optional
from common.blocks.base.schema import BaseSchema
from common.blocks.data import DataDocument

class DataUrl(AnyUrl):
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(
            {
                'format': 'data-url',
                'pattern': r'data:(.*);name=(.*);base64,(.*)',
            },
        )

class DataSourceEnvironmentSchema(BaseSchema):
    openai_key: str
class DataSourceInputSchema(BaseSchema):
    env: Optional[DataSourceEnvironmentSchema]

class DataSourceConfigurationSchema(BaseSchema):
    pass

class DataSourceOutputSchema(BaseSchema):
    documents: List[DataDocument]