from pydantic import Field

from .app_template_interface import AppTemplateInterface
from .app_template_interface import BaseSchema
from .app_template_interface import TemplatePage


class VoiceSummarizerBasicSchema(BaseSchema):
    voice_id: str = Field(
        title='Voice ID', description='Voice ID to be used, you can use https://api.elevenlabs.io/v1/voices to list all the available voices.', path='processors[2].config.voice_id',
    )
    summarize_instructions: str = Field(
        title='Summary Instructions', widget='textarea', description='Instructions to the summarizer model', path='processors[1].input.instructions',
    )


class VoiceSummarizerTemplate(AppTemplateInterface):
    """
    VoiceSummarizer Template
    """
    @staticmethod
    def slug() -> str:
        return 'voice-summarizer'

    @staticmethod
    def pages() -> list:
        return [
            TemplatePage(
                title='Settings',
                description='Configure voice summarizer. Make sure to add your ElevenLabs API key in Settings.',
                page_schema=VoiceSummarizerBasicSchema,
            ),
        ]
