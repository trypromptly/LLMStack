from typing import List
from typing import Optional

from pydantic import Field

from llmstack.apps.types.app_type_interface import AppTypeInterface
from llmstack.apps.types.app_type_interface import BaseSchema
from llmstack.processors.providers.api_processor_interface import DataUrl


class ChatAppConfigSchema(BaseSchema):
    input_template: str = Field(
        title='Page Content',
        default='', description='Content to show at the top of the chat window', widget='richtext',
    )
    welcome_message: str = Field(
        title='Welcome Message',
        default='', description='Welcome message from assistant to show when the chat session starts',
    )
    assistant_image: DataUrl = Field(
        title='Assistant Image',
        default='', description='Icon to show for the messages from assistant', accepts={'image/*': []}, widget='file',
    )
    window_color: str = Field(
        title='Primary Color of Chat Window',
        default='#477195', description='Color of the chat window', widget='color',
    )
    chat_bubble_text: Optional[str] = Field(
        title='App Bubble Text',
        description='Text to show in the app bubble when embedded in another page. If not provided, it shows chat bubble icon.', advanced_parameter=True,
    )
    chat_bubble_style: Optional[str] = Field(
        title='App Bubble Style',
        description='CSS style object to apply to the app bubble when embedded in another page', advanced_parameter=True, widget='textarea',
    )
    suggested_messages: List[str] = Field(
        title='Suggested messages', default=[], description='List of upto 3 suggested messages to show to the user', advanced_parameter=True,
    )


class ChatApp(AppTypeInterface[ChatAppConfigSchema]):
    @staticmethod
    def slug() -> str:
        return 'text-chat'

    @staticmethod
    def name() -> str:
        return 'Chat Bot'

    @staticmethod
    def description() -> str:
        return 'A chat application with an embeddable widget that can be used as a chatbot'
