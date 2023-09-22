from pydantic import Field

from .app_template_interface import AppTemplateInterface
from .app_template_interface import BaseSchema
from .app_template_interface import TemplatePage


class BrandCopyCheckerSchema(BaseSchema):
    brand_guidelines: str = Field(
        title='Brand information', description='Add your brand guidelines, company information etc., to verify copy against', widget='textarea', path='processors[0].input.system_message',
    )


class BrandCopyCheckerTemplate(AppTemplateInterface):
    """
    Brand copy checker template
    """
    @staticmethod
    def slug() -> str:
        return 'brand-copy-checker'

    @staticmethod
    def pages() -> list:
        return [
            TemplatePage(
                title='Configuration',
                description='Tune your copy checker',
                page_schema=BrandCopyCheckerSchema,
            ),
        ]
