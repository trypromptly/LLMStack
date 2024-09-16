import logging
from base64 import b64encode

from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.hubspot.views import HubspotOAuth2Adapter
from allauth.socialaccount.providers.spotify.views import SpotifyOAuth2Adapter

logger = logging.getLogger(__name__)


class ConnectionGitHubOAuth2Adapter(GitHubOAuth2Adapter):
    provider_id = "connection_github"


class ConnectionHubspotAdapter(HubspotOAuth2Adapter):
    provider_id = "connection_hubspot"


class ConnectionSpotifyOAuth2Adapter(SpotifyOAuth2Adapter):
    provider_id = "connection_spotify"

    @classmethod
    def refresh_token(cls, client_id, client_secret, refresh_token):
        import requests

        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + b64encode(f"{client_id}:{client_secret}".encode()).decode(),
        }
        form_data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        response = requests.post(cls.access_token_url, headers=headers, data=form_data)

        if response.status_code != 200:
            logger.error(f"Error refreshing token: {response.text}")
            return None
        return response.json()


class ConnectionGoogleOAuth2Adapter(GoogleOAuth2Adapter):
    provider_id = "connection_google"

    @classmethod
    def refresh_token(cls, client_id, client_secret, refresh_token):
        import requests

        response = requests.post(
            cls.access_token_url,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
        if response.status_code != 200:
            logger.error(f"Error refreshing token: {response.text}")
            return None
        return response.json()
