from django.apps import AppConfig

class ConnectionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'llmstack.connections'
    label = 'connections'
    
    def ready(self) -> None:
        from allauth.socialaccount import providers
        from llmstack.connections.handlers.custom_google_provider.provider import CustomGoogleProvider
        providers.registry.register(CustomGoogleProvider)

        return super().ready()
