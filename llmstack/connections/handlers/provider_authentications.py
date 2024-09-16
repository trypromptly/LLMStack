from datetime import datetime, timedelta, timezone

from llmstack.common.utils.prequests import post
from llmstack.connections.handlers.oauth2_providers.oauth_login_configurations import (
    GitHubLoginConfiguration,
    GoogleLoginConfiguration,
    HubspotLoginConfiguration,
    SpotifyLoginConfiguration,
)
from llmstack.connections.models import ConnectionType
from llmstack.connections.types import ConnectionTypeInterface


class OauthProviderLogin:
    @staticmethod
    def type() -> ConnectionType:
        return ConnectionType.OAUTH2

    def refresh_access_token(self, connection) -> str:
        refresh_token = connection.configuration["refresh_token"]
        client_id = connection.configuration["client_id"]
        client_secret = connection.configuration["client_secret"]
        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        response = post(token_url, data=payload)
        if response.status_code == 200:
            new_token = response.json().get("access_token")
            expires_in = response.json().get("expires_in")
            expires_at = timezone.now() + timedelta(seconds=int(expires_in))
            return new_token, expires_at.timestamp()
        else:
            return None

    def get_access_token(self, connection) -> str:
        expires_at = connection.configuration["expires_at"]
        if expires_at < datetime.datetime.now().timestamp():
            token, expires_at = self.refresh_access_token(connection)
            connection.configuration["token"] = token
            connection.configuration["expires_at"] = expires_at

        return connection


class SpotifyLogin(ConnectionTypeInterface[SpotifyLoginConfiguration], OauthProviderLogin):
    @staticmethod
    def name() -> str:
        return "Spotify Login"

    @staticmethod
    def provider_slug() -> str:
        return "spotify"

    @staticmethod
    def slug() -> str:
        return "spotify_oauth2"

    @staticmethod
    def description() -> str:
        return "Login to Spotify"

    @staticmethod
    def metadata() -> dict:
        return {
            "BtnText": "Login with Spotify",
            "BtnLink": "connections/spotify/login/",
            "RedirectUrl": "connections/spotify/callback/",
        }

    @classmethod
    def refresh_token(cls, configuration) -> SpotifyLoginConfiguration:
        from llmstack.connections.handlers.oauth2_providers.provider import (
            ConnectionSpotifyOAuth2Provider,
        )

        return ConnectionSpotifyOAuth2Provider.refresh_token(configuration)


class GoogleLogin(ConnectionTypeInterface[GoogleLoginConfiguration], OauthProviderLogin):
    @staticmethod
    def name() -> str:
        return "Google Login"

    @staticmethod
    def provider_slug() -> str:
        return "google"

    @staticmethod
    def slug() -> str:
        return "google_oauth2"

    @staticmethod
    def description() -> str:
        return "Login to Google"

    @staticmethod
    def metadata() -> dict:
        return {
            "BtnText": "Login with Google",
            "BtnLink": "connections/google/login/",
            "RedirectUrl": "connections/google/callback/",
        }

    @classmethod
    def refresh_token(cls, configuration) -> GoogleLoginConfiguration:
        from llmstack.connections.handlers.oauth2_providers.provider import (
            ConnectionGoogleOAuth2Provider,
        )

        return ConnectionGoogleOAuth2Provider.refresh_token(configuration)


class HubspotLogin(ConnectionTypeInterface[HubspotLoginConfiguration], OauthProviderLogin):
    @staticmethod
    def name() -> str:
        return "Hubspot Login"

    @staticmethod
    def provider_slug() -> str:
        return "hubspot"

    @staticmethod
    def slug() -> str:
        return "hubspot_oauth2"

    @staticmethod
    def description() -> str:
        return "Login to Hubspot"

    @staticmethod
    def metadata() -> dict:
        return {
            "BtnText": "Login with Hubspot",
            "BtnLink": "connections/hubspot/login/",
            "RedirectUrl": "connections/hubspot/callback/",
        }


class GitHubLogin(ConnectionTypeInterface[GitHubLoginConfiguration], OauthProviderLogin):
    @staticmethod
    def name() -> str:
        return "GitHub Login"

    @staticmethod
    def provider_slug() -> str:
        return "github"

    @staticmethod
    def slug() -> str:
        return "github_oauth2"

    @staticmethod
    def description() -> str:
        return "Login to GitHub"

    @staticmethod
    def metadata() -> dict:
        return {
            "BtnText": "Login with GitHub",
            "BtnLink": "connections/github/login/",
            "RedirectUrl": "connections/github/callback/",
        }
