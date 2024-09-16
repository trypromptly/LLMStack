from django.apps import AppConfig


class ConnectionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "llmstack.connections"
    label = "connections"

    def ready(self) -> None:
        from allauth.socialaccount import providers

        from llmstack.connections.handlers.oauth2_providers import (
            ConnectionGitHubOAuth2Provider,
            ConnectionGoogleOAuth2Provider,
            ConnectionHubspotProvider,
            ConnectionSpotifyOAuth2Provider,
        )

        providers.registry.register(ConnectionSpotifyOAuth2Provider)
        providers.registry.register(ConnectionHubspotProvider)
        providers.registry.register(ConnectionGitHubOAuth2Provider)
        providers.registry.register(ConnectionGoogleOAuth2Provider)

        return super().ready()
