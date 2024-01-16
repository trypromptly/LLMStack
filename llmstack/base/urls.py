from allauth.account.views import login, logout
from django.conf import settings
from django.urls import include, path, re_path

from .apis import ProfileViewSet

index_module = __import__(settings.INDEX_VIEW_MODULE, fromlist=[""])
index_view = getattr(index_module, "index")

urlpatterns = [
    path("logout", logout, name="logout"),
    path("accounts/", include("allauth.urls")),
    path(
        "api/profiles/me",
        ProfileViewSet.as_view({"get": "get", "patch": "patch"}),
    ),
    path(
        "api/profiles/me/flags",
        ProfileViewSet.as_view({"get": "get_flags"}),
    ),
    # Me
    path("api/me", ProfileViewSet.as_view({"get": "me"})),
]

if settings.INDEX_VIEW_MODULE != "llmstack.base.views":
    urlpatterns.append(path("login", login, name="login"))

urlpatterns.append(re_path(r"^(?!static\/)", index_view))
