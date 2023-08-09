from django.apps import AppConfig
from django.db.models.signals import post_save


class BaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'base'
    label = 'base'

    def ready(self):
        # call admin user if not exists
        try:
            from .management.commands.loadfixtures import Command
            Command().handle()
        except Exception as e:
            pass
        from django.contrib.auth.models import User
        from .models import create_user_profile, save_user_profile
        post_save.connect(create_user_profile, sender=User)
        post_save.connect(save_user_profile, sender=User)
