from pydantic import Field

from .app_template_interface import AppTemplateInterface
from .app_template_interface import BaseSchema
from .app_template_interface import TemplatePage


class CharacterChatbotBasicSchema(BaseSchema):
    header_message: str = Field(
        title='Header',
        widget='richtext',
        description='Content to show at the top of the chat window',
        path='config.input_template',
    )
    welcome_message: str = Field(
        title='Welcome Message',
        description='This is the message the character greets users with',
        path='config.welcome_message',
    )
    assistant_image: str = Field(
        title='Character Image',
        widget='file',
        description='Avatar to use for your character',
        path='config.assistant_image',
    )
    question_description: str = Field(
        title='Question help text',
        path='input_fields[0].description',
        description='Help text to show below the question input box',
    )
    character_behavior_message: str = Field(
        title='Character definition',
        widget='textarea',
        path='processors[0].input.system_message',
    )


class CharacterChatbotTemplate(AppTemplateInterface):
    """
    Character Chatbot Template
    """
    @staticmethod
    def slug() -> str:
        return 'character-chatbot'

    @staticmethod
    def pages() -> list:
        return [
            TemplatePage(
                title='Character configuration',
                description='Configure your character parameters',
                page_schema=CharacterChatbotBasicSchema,
            ),
        ]
