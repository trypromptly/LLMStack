from django.apps import AppConfig


class DatasourcesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "llmstack.data"
    label = "datasources"
