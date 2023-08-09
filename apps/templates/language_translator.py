from pydantic import Field

from .app_template_interface import AppTemplateInterface
from .app_template_interface import BaseSchema
from .app_template_interface import TemplatePage


class LanguageTranslatorSchema(BaseSchema):
    input_language: str = Field(
        title='Input language', description='Default value for the user input language', path='input_schema.properties.input_language.default',
    )
    output_language: str = Field(
        title='Output language', description='Default value for expected output language', path='input_schema.properties.output_language.default',
    )


class LanguageTranslatorTemplate(AppTemplateInterface):
    """
    Language translator template
    """
    @staticmethod
    def slug() -> str:
        return 'language-translator'

    @staticmethod
    def pages() -> list:
        return [
            TemplatePage(
                title='Settings',
                description='Configure your language translator',
                page_schema=LanguageTranslatorSchema,
            ),
        ]
