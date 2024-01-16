from pydantic import Field

from .app_template_interface import AppTemplateInterface
from .app_template_interface import BaseSchema
from .app_template_interface import TemplatePage


class MarketingContentGeneratorSchema(BaseSchema):
    brand_guidelines: str = Field(
        title='Brand information',
        description='Add your brand guidelines, company information etc., to set a personality for the content generator',
        widget='textarea',
        path='processors[0].input.system_message',
    )


class MarketingContentGeneratorTemplate(AppTemplateInterface):
    """
    Marketing content generator template
    """
    @staticmethod
    def slug() -> str:
        return 'marketing-content-generator'

    @staticmethod
    def pages() -> list:
        return [
            TemplatePage(
                title='Configuration',
                description='Tune your content generator',
                page_schema=MarketingContentGeneratorSchema,
            ),
        ]
