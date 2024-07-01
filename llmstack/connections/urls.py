import logging
from datetime import datetime

from allauth.socialaccount.helpers import render_authentication_error
from allauth.socialaccount.providers.base import ProviderException
from allauth.socialaccount.providers.base.constants import AuthAction, AuthError
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from allauth.socialaccount.providers.oauth2.views import (
    OAuth2CallbackView,
    OAuth2LoginView,
)
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import path
from requests import RequestException

from llmstack.base.models import Profile
from llmstack.connections.models import Connection, ConnectionStatus

from .apis import ConnectionsViewSet
from .handlers.google import GoogleAdapter
from .handlers.hubspot import HubspotAdapter

logger = logging.getLogger(__name__)

# Copy of allauth.socialaccount.providers.oauth2.views.OAuth2LoginView


class CustomOAuth2LoginView(OAuth2LoginView):
    def login(self, request, *args, **kwargs):
        provider = self.adapter.get_provider()
        app = provider.app
        client = self.get_client(request, app)
        action = request.GET.get("action", AuthAction.AUTHENTICATE)
        auth_url = self.adapter.authorize_url
        auth_params = provider.get_auth_params(request, action)

        pkce_params = provider.get_pkce_params()
        code_verifier = pkce_params.pop("code_verifier", None)
        auth_params.update(pkce_params)
        if code_verifier:
            request.session["pkce_code_verifier"] = code_verifier

        try:
            return HttpResponseRedirect(
                client.get_redirect_url(
                    auth_url,
                    auth_params,
                ),
            )
        except OAuth2Error as e:
            return render_authentication_error(
                request,
                provider.id,
                exception=e,
            )


# Copy of allauth.socialaccount.providers.oauth2.views.OAuth2CallbackView


class CustomOAuth2CallbackView(OAuth2CallbackView):
    def dispatch(self, request, *args, **kwargs):
        provider = self.adapter.get_provider()
        if "error" in request.GET or "code" not in request.GET:
            # Distinguish cancel from error
            auth_error = request.GET.get("error", None)
            if auth_error == self.adapter.login_cancelled_error:
                error = AuthError.CANCELLED
            else:
                error = AuthError.UNKNOWN
            return render_authentication_error(
                request,
                provider,
                error=error,
            )
        app = self.adapter.get_provider().get_app(self.request)
        client = self.get_client(self.request, app)
        try:
            access_token = self.adapter.get_access_token_data(
                request,
                app,
                client,
            )
            token = self.adapter.parse_token(access_token)
            if app.pk:
                token.app = app
            result = self.adapter.complete_login(
                request,
                app,
                token,
                response=access_token,
            )
            profile = Profile.objects.get(user=request.user)
            connection_objects = profile.get_connection_by_type(
                self.adapter.get_connection_type_slug(),
            )

            # Get the latest connection object for this connection type, work
            # with the assumption
            connection_objects.sort(
                key=lambda x: datetime.strptime(
                    x["created_at"],
                    "%Y-%m-%dT%H:%M:%S.%f",
                ),
                reverse=True,
            )
            latest_connection = connection_objects[0]

            connection = Connection(**latest_connection)
            connection.status = ConnectionStatus.ACTIVE
            connection.configuration = result.model_dump()

            profile.add_connection(connection.model_dump())

            return HttpResponseRedirect("/settings")
        except (
            PermissionDenied,
            OAuth2Error,
            RequestException,
            ProviderException,
        ) as e:
            return render_authentication_error(
                request,
                self.adapter.provider_id,
                exception=e,
            )


urlpatterns = [
    path(
        "api/connection_types",
        ConnectionsViewSet.as_view({"get": "get_connection_types"}),
    ),
    path(
        "api/connections",
        ConnectionsViewSet.as_view({"get": "list"}),
    ),
    path(
        "api/connections/<str:uid>/access_token",
        ConnectionsViewSet.as_view({"get": "get_access_token"}),
    ),
    path(
        "api/connections/<str:uid>",
        ConnectionsViewSet.as_view(
            {
                "get": "get",
                "post": "post",
                "patch": "patch",
                "delete": "delete",
            },
        ),
    ),
    path(
        "connections/hubspot/login/",
        CustomOAuth2LoginView.adapter_view(HubspotAdapter),
        name="hubspot_connection_login",
    ),
    path(
        "connections/hubspot/login/callback/",
        CustomOAuth2CallbackView.adapter_view(HubspotAdapter),
        name="hubspot_connection_callback",
    ),
    path(
        "connections/google/login/",
        CustomOAuth2LoginView.adapter_view(GoogleAdapter),
        name="google_connection_login",
    ),
    path(
        "connections/google/login/callback/",
        CustomOAuth2CallbackView.adapter_view(GoogleAdapter),
        name="google_connection_callback",
    ),
]
