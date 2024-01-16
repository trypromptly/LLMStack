from typing import List
from typing import Optional

from pydantic import Field

from .app_template_interface import AppTemplateInterface
from .app_template_interface import BaseSchema
from .app_template_interface import TemplatePage


class VoiceAnswersBasicSchema(BaseSchema):
    voice_id: str = Field(
        title='Voice ID',
        description='Voice ID to be used, you can use https://api.elevenlabs.io/v1/voices to list all the available voices.',
        path='processors[2].config.voice_id',
    )
    ai_system_message: str = Field(
        title='AI System Message',
        widget='textarea',
        description='System instructions to the ChatGPT model',
        path='processors[1].input.system_message',
    )


class VoiceAnswersTemplate(AppTemplateInterface):
    """
    AI Augmented Search Template
    """
    @staticmethod
    def slug() -> str:
        return 'voice-answers'

    @staticmethod
    def pages() -> list:
        return [
            TemplatePage(
                title='Settings',
                description='Configure voice answers parameters. Make sure to add your ElevenLabs API key in Settings.',
                page_schema=VoiceAnswersBasicSchema,
            ),
        ]
