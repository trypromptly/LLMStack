from typing import List

from pydantic import Field

from llmstack.apps.types.app_type_interface import AppTypeInterface
from llmstack.apps.types.app_type_interface import BaseSchema


class WebAppConfigSchema(BaseSchema):
    input_template: str = Field(
        title='Page Content',
        default='', description='Content to show at the top of the App page before the input form', widget='richtext',
    )
    allowed_sites: List[str] = Field(
        title='Allowed Sites to Embed this App',
        default=[], description='List of domains that are allowed to embed this app. Leave empty to allow all sites.', advanced_parameter=True, hidden=True,
    )


class WebApp(AppTypeInterface[WebAppConfigSchema]):
    @staticmethod
    def slug() -> str:
        return 'web'
