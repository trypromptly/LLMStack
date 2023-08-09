from enum import Enum
from typing import List
from typing import Optional

from pydantic import Field

from .app_template_interface import AppTemplateInterface
from .app_template_interface import BaseSchema
from .app_template_interface import TemplatePage


class FomalityEnum(str, Enum):
    Formal = 'Formal'
    Informal = 'Informal'
    Friendly = 'Friendly'
    Serious = 'Serious'
    Professional = 'Professional'
    Casual = 'Casual'


class ToneEnum(str, Enum):
    Personable = 'Personable'
    Confident = 'Confident'
    Empathetic = 'Empathetic'
    Engaging = 'Engaging'
    Direct = 'Direct'
    Witty = 'Witty'


class VocabularyEnum(str, Enum):
    Basic = 'Basic'
    Intermediate = 'Intermediate'
    Advanced = 'Advanced'


class AIWritingAssistantSetting(BaseSchema):
    formality: FomalityEnum = Field(
        description='Formality of the text', path='input_schema.properties.formality.default',
    )

    tone: ToneEnum = Field(
        description='Tone of the text',
        path='input_schema.properties.tone.default',
    )

    vocabulary: VocabularyEnum = Field(
        description='Vocabulary of the text',
        path='input_schema.properties.vocabulary.default',
    )

    profession: str = Field(
        description='Profession of the writer',
        path='input_schema.properties.profession.default',
    )


class AIWritingAssistantTemplate(AppTemplateInterface):
    """
    AI Writing Assistant Template
    """
    @staticmethod
    def slug() -> str:
        return 'ai-writing-assistant'

    @staticmethod
    def pages() -> list:
        return [
            TemplatePage(
                title='Writing Style Settings',
                description='Configure your writing style parameters',
                page_schema=AIWritingAssistantSetting,
            ),
        ]
