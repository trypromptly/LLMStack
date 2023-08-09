from pydantic import Field

from .app_template_interface import AppTemplateInterface
from .app_template_interface import BaseSchema
from .app_template_interface import TemplatePage


class DataExtractorSchema(BaseSchema):
    features: str = Field(
        title='Features to extract', description='List of features and the format to extract from input. For example, "Name and birthday of all candidates in the text"', widget='textarea', path='processors[0].input.messages[1].content',
    )


class DataExtractorTemplate(AppTemplateInterface):
    """
    Data extractor template
    """
    @staticmethod
    def slug() -> str:
        return 'data-extractor'

    @staticmethod
    def pages() -> list:
        return [
            TemplatePage(
                title='Configuration',
                description='Feature definition',
                page_schema=DataExtractorSchema,
            ),
        ]
