from typing import List, Optional

from llmstack.connections.handlers import Oauth2BaseConfiguration


class SpotifyLoginConfiguration(Oauth2BaseConfiguration):
    provider_id: str = "connection_spotify"
    scope: Optional[str] = None
    extra_data: Optional[dict] = None


class GoogleLoginConfiguration(Oauth2BaseConfiguration):
    provider_id: str = "connection_google"
    scope: Optional[List[str]] = None
    extra_data: Optional[dict] = None


class HubspotLoginConfiguration(Oauth2BaseConfiguration):
    provider_id: str = "connection_hubspot"
    scope: Optional[List[str]] = None
    extra_data: Optional[dict] = None


class GitHubLoginConfiguration(Oauth2BaseConfiguration):
    provider_id: str = "connection_github"
    scope: Optional[List[str]] = None
    extra_data: Optional[dict] = None
