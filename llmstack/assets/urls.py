from django.urls import path

from . import apis

urlpatterns = [
    path("api/assets/<str:category>/<str:uuid>", apis.AssetViewSet.as_view({"get": "get"})),
]
