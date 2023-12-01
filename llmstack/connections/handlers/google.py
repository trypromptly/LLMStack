import logging
from typing import List, Optional 
from llmstack.connections.handlers import Oauth2BaseConfiguration
from llmstack.connections.handlers.custom_google_provider.provider import CustomGoogleProvider
from llmstack.connections.types import ConnectionTypeInterface
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from llmstack.connections.models import ConnectionType
import jwt

logger = logging.getLogger(__name__)

class GoogleAdapter(GoogleOAuth2Adapter):
    provider_id = CustomGoogleProvider.id 
    
    def get_connection_type_slug(self):
        return 'google_oauth2'
    
    def get_callback_url(self, request, app):
        from django.urls import reverse
        from allauth.utils import build_absolute_uri

        callback_url = reverse('google_connection_callback')
        protocol = self.redirect_uri_protocol
        redirect_uri = build_absolute_uri(request, callback_url, protocol)
        return redirect_uri
    
    def complete_login(self, request, app, token, **kwargs):
        response = kwargs.get("response")
        try:
            token = response["access_token"]
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
        extra_data = {
            'token': token,
            'scope': response['scope'],
            'token_type': response['token_type'],
            'refresh_token': response['refresh_token'] if 'refresh_token' in response else '',
        }
        return GoogleLoginConfiguration(**extra_data)
        
class GoogleLoginConfiguration(Oauth2BaseConfiguration):
    refresh_token: Optional[str]
    scope: Optional[str]
    token_type: Optional[str]

class GoogleLogin(ConnectionTypeInterface[GoogleLoginConfiguration]):
    @staticmethod
    def name() -> str:
        return 'Google Login'

    @staticmethod
    def provider_slug() -> str:
        return 'Google'

    @staticmethod
    def slug() -> str:
        return 'google_oauth2'

    @staticmethod
    def description() -> str:
        return 'Login to Google'
    
    @staticmethod
    def type() -> ConnectionType:
        return ConnectionType.OAUTH2
    
    @staticmethod
    def metadata() -> dict:
        return {
            'BtnText': 'Login with Google',
            'BtnLink': 'connections/google/login/',
            'RedirectUrl': 'connections/google/callback/',
        }