from pydantic import Field

from .app_template_interface import AppTemplateInterface
from .app_template_interface import BaseSchema
from .app_template_interface import TemplatePage


class FileChatbotBasicSchema(BaseSchema):
    header_message: str = Field(
        title='Header', widget='richtext',
        description='Content to show at the top of the chat window', path='config.input_template',
    )
    welcome_message: str = Field(
        title='Welcome Message',
        description='This is the message the chatbot greets user with', path='config.welcome_message',
    )
    assistant_image: str = Field(
        title='Chatbot Image', widget='file',
        description='Avatar to use for your chatbot', path='config.assistant_image',
    )
    question_description: str = Field(
        title='Question help text', path='input_fields[1].description', description='Help text to show below the question input box',
    )


class FileChatbotTemplate(AppTemplateInterface):
    """
    FileChatbot Template
    """
    @staticmethod
    def slug() -> str:
        return 'file-chatbot'

    @staticmethod
    def pages() -> list:
        return [
            TemplatePage(
                title='Chatbot configuration',
                description='Configure your file chatbot',
                page_schema=FileChatbotBasicSchema,
            ),
        ]
