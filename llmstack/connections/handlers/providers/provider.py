import logging
from typing import Optional

from allauth.socialaccount.providers.github.provider import GitHubProvider
from allauth.socialaccount.providers.google.provider import GoogleProvider
from allauth.socialaccount.providers.hubspot.provider import HubspotProvider
from allauth.socialaccount.providers.spotify.provider import SpotifyOAuth2Provider
from anthropic import BaseModel

from llmstack.connections.handlers.providers.oauth_login_configurations import (
    GitHubLoginConfiguration,
    GoogleLoginConfiguration,
    HubspotLoginConfiguration,
    SpotifyLoginConfiguration,
)

from .views import (
    ConnectionGitHubOAuth2Adapter,
    ConnectionGoogleOAuth2Adapter,
    ConnectionHubspotAdapter,
    ConnectionSpotifyOAuth2Adapter,
)

logger = logging.getLogger(__name__)


class SocialApp(BaseModel):
    connection_type_slug: str
    provider: str
    provider_id: str
    name: str
    client_id: Optional[str] = None
    secret: Optional[str] = None
    key: Optional[str] = None
    settings: Optional[dict] = None


class ConnectionGoogleOAuth2Provider(GoogleProvider):
    uses_apps = False
    id = "connection_google"
    name = "Google"
    oauth2_adapter_class = ConnectionGoogleOAuth2Adapter

    def __init__(self, request, app=None):
        from django.conf import settings

        self.request = request
        app_settings = settings.SOCIALACCOUNT_PROVIDERS.get(self.id, {}).get("APP")
        self.app = SocialApp(
            connection_type_slug="google_oauth2",
            provider=self.id,
            provider_id=self.id,
            name=self.name,
            **app_settings,
        )

    def get_app(self, request, config=None):
        return self.app

    def sociallogin_from_response(self, request, response):
        return GoogleLoginConfiguration(extra_data=response)


class ConnectionSpotifyOAuth2Provider(SpotifyOAuth2Provider):
    uses_apps = False
    id = "connection_spotify"
    name = "Spotify"
    oauth2_adapter_class = ConnectionSpotifyOAuth2Adapter

    def __init__(self, request, app=None):
        from django.conf import settings

        self.request = request
        app_settings = settings.SOCIALACCOUNT_PROVIDERS.get(self.id, {}).get("APP")
        self.app = SocialApp(
            connection_type_slug="spotify_oauth2",
            provider=self.id,
            provider_id=self.id,
            name=self.name,
            **app_settings,
        )

    def get_app(self, request, config=None):
        return self.app

    def sociallogin_from_response(self, request, response):
        return SpotifyLoginConfiguration(extra_data=response)


class ConnectionHubspotProvider(HubspotProvider):
    uses_apps = False
    id = "connection_hubspot"
    name = "Hubspot"
    oauth2_adapter_class = ConnectionHubspotAdapter

    def __init__(self, request, app=None):
        from django.conf import settings

        self.request = request
        app_settings = settings.SOCIALACCOUNT_PROVIDERS.get(self.id, {}).get("APP")
        self.app = SocialApp(
            connection_type_slug="hubspot_oauth2",
            provider=self.id,
            provider_id=self.id,
            name=self.name,
            **app_settings,
        )

    def get_app(self, request, config=None):
        return self.app

    def sociallogin_from_response(self, request, response):
        return HubspotLoginConfiguration(extra_data=response)


class ConnectionGitHubOAuth2Provider(GitHubProvider):
    uses_apps = False
    id = "connection_github"
    name = "GitHub"
    oauth2_adapter_class = ConnectionGitHubOAuth2Adapter

    def __init__(self, request, app=None):
        from django.conf import settings

        self.request = request
        app_settings = settings.SOCIALACCOUNT_PROVIDERS.get(self.id, {}).get("APP")
        self.app = SocialApp(
            connection_type_slug="github_oauth2",
            provider=self.id,
            provider_id=self.id,
            name=self.name,
            **app_settings,
        )

    def get_app(self, request, config=None):
        return self.app

    def sociallogin_from_response(self, request, response):
        return GitHubLoginConfiguration(extra_data=response)
