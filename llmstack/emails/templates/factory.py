from llmstack.emails.templates.template_interface import TemplateInterface
from django.conf import settings
from django.utils.module_loading import import_string


class DefaultTemplate(TemplateInterface):
    def __init__(self, **kwargs):
        pass

    def get_to(self):
        return []


class DefaultEmailTemplateFactory:
    @staticmethod
    def get_template_by_name(name: str) -> TemplateInterface:
        return DefaultTemplate


EmailTemplateFactory = import_string(settings.EMAIL_TEMPLATE_FACTORY_CLASS)
