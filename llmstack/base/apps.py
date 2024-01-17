from django.apps import AppConfig
from django.db.models.signals import post_save


class BaseConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "llmstack.base"
    label = "base"

    def ready(self):
        from django.contrib.auth.models import User

        from .models import create_user_profile

        post_save.connect(create_user_profile, sender=User)

        # call admin user if not exists
        try:
            from .management.commands.loadfixtures import Command

            Command().handle()
        except Exception:
            pass
