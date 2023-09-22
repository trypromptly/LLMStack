from llmstack.emails.templates.template_interface import TemplateInterface
from django.utils.module_loading import import_string
from django.conf import settings


class AbstractEmailSender:
    def send(self, schedule: int = None):
        pass


class DefaultEmailSender(AbstractEmailSender):
    def __init__(self, template: TemplateInterface):
        pass


EmailSender = import_string(settings.EMAIL_SENDER_CLASS)
