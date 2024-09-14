import logging

from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.hubspot.views import HubspotOAuth2Adapter
from allauth.socialaccount.providers.spotify.views import SpotifyOAuth2Adapter

logger = logging.getLogger(__name__)


class ConnectionGitHubOAuth2Adapter(GitHubOAuth2Adapter):
    pass


class ConnectionHubspotAdapter(HubspotOAuth2Adapter):
    pass


class ConnectionSpotifyOAuth2Adapter(SpotifyOAuth2Adapter):
    provider_id = "connection_spotify"


class ConnectionGoogleOAuth2Adapter(GoogleOAuth2Adapter):
    provider_id = "connection_google"
