import logging
from typing import List, Optional

import requests
from allauth.socialaccount.providers.hubspot.views import HubspotOAuth2Adapter

from llmstack.connections.handlers import Oauth2BaseConfiguration
from llmstack.connections.models import ConnectionType
from llmstack.connections.types import ConnectionTypeInterface

logger = logging.getLogger(__name__)


class HubspotAdapter(HubspotOAuth2Adapter):
    def get_connection_type_slug(self):
        return "hubspot_oauth2"

    def get_callback_url(self, request, app):
        from allauth.utils import build_absolute_uri
        from django.urls import reverse

        callback_url = reverse("hubspot_connection_callback")
        protocol = self.redirect_uri_protocol
        redirect_uri = build_absolute_uri(request, callback_url, protocol)
        return redirect_uri

    def complete_login(self, request, app, token, **kwargs):
        headers = {"Content-Type": "application/json"}
        response = requests.get(
            "{0}/{1}".format(self.profile_url, token.token),
            headers=headers,
        )
        response.raise_for_status()
        extra_data = response.json()
        provider = self.get_provider()
        uid = provider.extract_uid(extra_data)  # noqa

        extra_data = provider.extract_extra_data(extra_data)
        return HubspotLoginConfiguration(**extra_data)


class HubspotLoginConfiguration(Oauth2BaseConfiguration):
    user: Optional[str] = None
    hub_domain: Optional[str] = None
    scopes: Optional[List[str]] = None
    hub_id: Optional[str] = None
    app_id: Optional[str] = None
    expires_in: Optional[int] = None
    user_id: Optional[int] = None
    token_type: Optional[str] = None


class HubspotLogin(ConnectionTypeInterface[HubspotLoginConfiguration]):
    @staticmethod
    def name() -> str:
        return "Hubspot Login"

    @staticmethod
    def provider_slug() -> str:
        return "Hubspot"

    @staticmethod
    def slug() -> str:
        return "hubspot_oauth2"

    @staticmethod
    def description() -> str:
        return "Login to Hubspot"

    @staticmethod
    def type() -> ConnectionType:
        return ConnectionType.OAUTH2

    @staticmethod
    def metadata() -> dict:
        return {
            "BtnText": "Login with Hubspot",
            "BtnLink": "connections/hubspot/login/",
            "RedirectUrl": "connections/hubspot/callback/",
        }

    def get_access_token(self, connection) -> str:
        return connection
