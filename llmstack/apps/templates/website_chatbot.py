from typing import List
from typing import Optional

from pydantic import Field

from .app_template_interface import AppTemplateInterface
from .app_template_interface import BaseSchema
from .app_template_interface import TemplatePage


class WebsiteChatbotBasicSchema(BaseSchema):
    welcome_message: str = Field(
        title='Welcome Message',
        description='This is the message the chatbot greets users with', path='config.welcome_message',
    )
    assistant_image: str = Field(
        title='Assistant Image', widget='file',
        description='Icon to show for the messages from assistant', path='config.assistant_image',
    )


class WebsiteChatbotDataSchema(BaseSchema):
    datasource: List[str] = Field(
        description='Select the data for the chatbot to answer from. Click on the icon to the right to add new data', widget='datasource', path='processors[0].config.datasource',
    )


class WebsiteChatbotAdvancedSchema(BaseSchema):
    window_color: str = Field(
        title='Primary Color of Chat Window',
        description='Color of the chat window', widget='color', path='config.window_color',
    )
    chat_bubble_text: Optional[str] = Field(
        title='App Bubble Text',
        description='Text to show in the app bubble when embedded in another page. Leave empty to show a chat bubble icon.', path='config.chat_bubble_text',
    )
    chat_bubble_style: Optional[str] = Field(
        title='App Bubble Style',
        description='CSS style object to apply to the app bubble when embedded in another page. Leave empty to use a chat bubble icon', advanced_parameter=True, widget='textarea', path='config.chat_bubble_style',
    )


class WebsiteChatbotTemplate(AppTemplateInterface):
    """
    Website Chatbot Template
    """
    @staticmethod
    def slug() -> str:
        return 'website-chatbot'

    @staticmethod
    def pages() -> list:
        return [
            TemplatePage(
                title='Basic',
                description='Configure your Chatbot',
                page_schema=WebsiteChatbotBasicSchema,
            ),
            TemplatePage(
                title='Data',
                description='Provide data for your Chatbot',
                page_schema=WebsiteChatbotDataSchema,
            ),
            TemplatePage(
                title='Finish',
                description='Final touches',
                page_schema=WebsiteChatbotAdvancedSchema,
            ),
        ]
