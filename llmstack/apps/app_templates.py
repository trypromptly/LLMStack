from .models import App
from .models import AppTemplate
from .templates.ai_augmented_search import AIAugmentedSearchTemplate
from .templates.ai_writing_assistant import AIWritingAssistantTemplate
from .templates.app_template_interface import AppTemplateInterface
from .templates.brand_copy_checker import BrandCopyCheckerTemplate
from .templates.character_chatbot import CharacterChatbotTemplate
from .templates.data_extractor import DataExtractorTemplate
from .templates.file_chatbot import FileChatbotTemplate
from .templates.hr_assistant import HrAssistantTemplate
from .templates.language_translator import LanguageTranslatorTemplate
from .templates.marketing_content_generator import MarketingContentGeneratorTemplate
from .templates.voice_answers import VoiceAnswersTemplate
from .templates.voice_chat import VoiceChatTemplate
from .templates.voice_summarizer import VoiceSummarizerTemplate
from .templates.website_chatbot import WebsiteChatbotTemplate
# Import all app templates here


class AppTemplateFactory:
    """
    Factory class for App templates
    """
    @staticmethod
    def get_app_template_handler(app_template: AppTemplate) -> AppTemplateInterface:
        subclasses = AppTemplateInterface.__subclasses__()
        for subclass in subclasses:
            if subclass.slug() == app_template.slug.lower():
                return subclass

        return None
