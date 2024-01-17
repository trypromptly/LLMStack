import datetime
import logging
from datetime import timedelta
from typing import Optional

import jwt
import requests
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from django.utils import timezone

from llmstack.connections.handlers import Oauth2BaseConfiguration
from llmstack.connections.handlers.custom_google_provider.provider import (
    CustomGoogleProvider,
)
from llmstack.connections.models import ConnectionType
from llmstack.connections.types import ConnectionTypeInterface

logger = logging.getLogger(__name__)


class GoogleAdapter(GoogleOAuth2Adapter):
    provider_id = CustomGoogleProvider.id

    def get_connection_type_slug(self):
        return "google_oauth2"

    def get_callback_url(self, request, app):
        from allauth.utils import build_absolute_uri
        from django.urls import reverse

        callback_url = reverse("google_connection_callback")
        protocol = self.redirect_uri_protocol
        redirect_uri = build_absolute_uri(request, callback_url, protocol)
        return redirect_uri

    def complete_login(self, request, app, token, **kwargs):
        response = kwargs.get("response")
        try:
            jwt.decode(
                response["id_token"],
                # Since the token was received by direct communication
                # protected by TLS between this library and Google, we
                # are allowed to skip checking the token signature
                # according to the OpenID Connect Core 1.0
                # specification.
                # https://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation
                options={
                    "verify_signature": False,
                    "verify_iss": True,
                    "verify_aud": True,
                    "verify_exp": True,
                },
                issuer=self.id_token_issuer,
                audience=app.client_id,
            )
        except jwt.PyJWTError as e:
            raise Exception("Invalid id_token") from e
        parsed_token_data = self.parse_token(response)
        extra_data = {
            "token": parsed_token_data.token,
            "refresh_token": parsed_token_data.token_secret,
            "expires_at": parsed_token_data.expires_at.timestamp(),
            "client_id": app.client_id,
            "client_secret": app.secret,
        }
        return GoogleLoginConfiguration(**extra_data)


class GoogleLoginConfiguration(Oauth2BaseConfiguration):
    refresh_token: Optional[str]
    scope: Optional[str]
    token_type: Optional[str]
    expires_at: Optional[float]
    client_id: Optional[str]
    client_secret: Optional[str]


class GoogleLogin(ConnectionTypeInterface[GoogleLoginConfiguration]):
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
    def type() -> ConnectionType:
        return ConnectionType.OAUTH2

    @staticmethod
    def metadata() -> dict:
        return {
            "BtnText": "Login with Google",
            "BtnLink": "connections/google/login/",
            "RedirectUrl": "connections/google/callback/",
        }

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
        response = requests.post(token_url, data=payload)
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
