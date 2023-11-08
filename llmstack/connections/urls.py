from django.http import HttpResponseRedirect
from django.urls import path

from llmstack.base.models import Profile
from .apis import ConnectionsViewSet

from allauth.socialaccount.providers.oauth2.views import (
    OAuth2CallbackView,
    OAuth2LoginView,
)

from .handlers.hubspot import HubspotAdapter

from requests import RequestException

from django.core.exceptions import PermissionDenied

from allauth.socialaccount.helpers import (
    render_authentication_error,
)
from allauth.socialaccount.providers.base import ProviderException
from allauth.socialaccount.providers.base.constants import (
    AuthError,
    AuthAction
)
from allauth.socialaccount.providers.oauth2.client import (
    OAuth2Error,
)
from allauth.socialaccount.providers.base.mixins import OAuthLoginMixin
from allauth.socialaccount.providers.oauth2.views import OAuth2View

import logging 
logger = logging.getLogger(__name__)
class CustomOAuth2CallbackView(OAuth2CallbackView):
    def dispatch(self, request, *args, **kwargs):
        if "error" in request.GET or "code" not in request.GET:
            # Distinguish cancel from error
            auth_error = request.GET.get("error", None)
            if auth_error == self.adapter.login_cancelled_error:
                error = AuthError.CANCELLED
            else:
                error = AuthError.UNKNOWN
            return render_authentication_error(
                request, self.adapter.provider_id, error=error
            )
        app = self.adapter.get_provider().get_app(self.request)
        client = self.get_client(self.request, app)
        try:
            access_token = self.adapter.get_access_token_data(request, app, client)
            token = self.adapter.parse_token(access_token)
            token.app = app
            conn_object = self.adapter.complete_login(request, app, token, response=access_token)
            profile = Profile.objects.get(user=request.user)
            return HttpResponseRedirect('/settings')
        except (
            PermissionDenied,
            OAuth2Error,
            RequestException,
            ProviderException,
        ) as e:
            return render_authentication_error(
                request, self.adapter.provider_id, exception=e
            )
 

urlpatterns = [
    path('api/connection_types',
         ConnectionsViewSet.as_view({'get': 'get_connection_types'})),

    path('api/connections', ConnectionsViewSet.as_view({'get': 'list'})),

    path(
        'api/connections/<str:uid>',
        ConnectionsViewSet.as_view(
            {'get': 'get', 'post': 'post', 'patch': 'patch', 'delete': 'delete'}),
    ),
    path('connections/hubspot/login/', OAuth2LoginView.adapter_view(HubspotAdapter), name='hubspot_connection_login'),
    path('connections/hubspot/login/callback/', CustomOAuth2CallbackView.adapter_view(HubspotAdapter), name='hubspot_connection_callback'),
]
