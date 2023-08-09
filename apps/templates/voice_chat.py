from typing import List

from pydantic import Field

from .app_template_interface import AppTemplateInterface
from .app_template_interface import BaseSchema
from .app_template_interface import TemplatePage


class VoiceChatBasicSchema(BaseSchema):
    assistant_image: str = Field(
        title='Assistant Image', widget='file',
        description='Icon to show for the messages from assistant', path='config.assistant_image',
    )
    assistant_voice: str = Field(
        title='Assistant Speech Voice',
        description='ElevenLabs Voice ID to use for your assistant.  You can use https://api.elevenlabs.io/v1/voices to list all the available voices.', path='processors[2].config.voice_id',
    )
    speech_model: str = Field(
        title='Speech Model',
        description='ElevenLabs speech model to use for your assistant. You can query them using GET https://api.elevenlabs.io/v1/models.', path='processors[2].config.model_id',
    )


class VoiceChatAdvancedSchema(BaseSchema):
    datasource: List[str] = Field(
        description='Select the data for the chatbot to answer from. Click on the icon to the right to add new data', widget='datasource', path='processors[1].config.datasource',
    )
    speech_to_text_prompt: str = Field(
        title='Speech to Text Prompt',
        description='Optional prompt to guide the Whisper model for text generation from speech', path='processors[0].input.prompt',
    )


class VoiceChatTemplate(AppTemplateInterface):
    """
    Voice chat template
    """
    @staticmethod
    def slug() -> str:
        return 'voice-chat'

    @staticmethod
    def pages() -> list:
        return [
            TemplatePage(
                title='Basic',
                description='Configure voice settings',
                page_schema=VoiceChatBasicSchema,
            ),
            TemplatePage(
                title='Finish',
                description='Supporting Data',
                page_schema=VoiceChatAdvancedSchema,
            ),
        ]
