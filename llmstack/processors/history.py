from django.utils.module_loading import import_string
from django.conf import settings

from llmstack.processors.models import RunEntry


class AbstractHistoryStore:
    @staticmethod
    def persist(data: RunEntry, **kwargs):
        raise NotImplementedError()


class DefaultHistoryStore(AbstractHistoryStore):
    @staticmethod
    def persist(data: RunEntry, **kwargs):
        data.save()


HistoryStore = import_string(settings.HISTORY_STORE_CLASS)
