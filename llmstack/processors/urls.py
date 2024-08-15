from django.urls import path

from . import apis

urlpatterns = [
    # APIs
    # Authentication
    path("api/login", apis.LoginView.as_view()),
    path("api/logout", apis.LogoutAPIView.as_view()),
    # Backends
    path(
        "api/apibackends/",
        apis.ApiBackendViewSet.as_view({"get": "filtered"}),
    ),
    path("api/apibackends", apis.ApiBackendViewSet.as_view({"get": "list"})),
    path("api/apiproviders", apis.ApiProviderViewSet.as_view({"get": "list"})),
    # History
    path("api/history", apis.HistoryViewSet.as_view({"get": "list"})),
    path(
        "api/history/download",
        apis.HistoryViewSet.as_view({"post": "download"}),
    ),
    path(
        "api/history/sessions",
        apis.HistoryViewSet.as_view({"get": "list_sessions"}),
    ),
    path(
        "api/history/<str:request_uuid>",
        apis.HistoryViewSet.as_view({"get": "get", "patch": "patch"}),
    ),
]
