from django.urls import path

from . import apis

urlpatterns = [
    # App types
    path("api/app_types", apis.AppTypeViewSet.as_view({"get": "get"})),
    path("api/app_types", apis.AppTypeViewSet.as_view({"get": "get"})),
    # Apps
    path(
        "api/apps/templates",
        apis.AppViewSet.as_view({"get": "getTemplates"}),
    ),
    path(
        "api/apps/templates/<str:slug>",
        apis.AppViewSet.as_view({"get": "getTemplates"}),
    ),
    path("api/apps", apis.AppViewSet.as_view({"get": "get", "post": "post"})),
    path("api/apps/shared", apis.AppViewSet.as_view({"get": "getShared"})),
    path(
        "api/apps/<str:uid>",
        apis.AppViewSet.as_view(
            {"get": "get", "patch": "patch", "delete": "delete"},
        ),
    ),
    path(
        "api/apps/<str:uid>/processors/<str:id>/run",
        apis.AppViewSet.as_view({"post": "processor_run"}),
    ),
    path("api/apps/<str:app_uuid>/run", apis.AppViewSet.as_view({"post": "run"})),
    path(
        "api/apps/<str:uid>/versions",
        apis.AppViewSet.as_view({"get": "versions"}),
    ),
    path(
        "api/apps/<str:uid>/versions/<str:version>",
        apis.AppViewSet.as_view({"get": "versions"}),
    ),
    path(
        "api/apps/<str:uid>/discord/run",
        apis.DiscordViewSet.as_view({"post": "run_async"}),
    ),
    path(
        "api/apps/<str:uid>/slack/run",
        apis.SlackViewSet.as_view({"post": "run_async"}),
    ),
    path(
        "api/apps/<str:uid>/twiliosms/run",
        apis.TwilioSMSViewSet.as_view({"post": "run_async"}),
    ),
    path(
        "api/apps/<str:uid>/twiliovoice/run",
        apis.AppViewSet.as_view({"post": "run_twiliovoice"}),
    ),
    path(
        "api/apps/<str:uid>/run/<str:session_id>",
        apis.AppViewSet.as_view({"post": "run"}),
    ),
    path(
        "api/apps/<str:uid>/publish",
        apis.AppViewSet.as_view({"post": "publish"}),
    ),
    path(
        "api/apps/<str:uid>/unpublish",
        apis.AppViewSet.as_view({"post": "unpublish"}),
    ),
    path(
        "api/apps/<str:uid>/testsets",
        apis.AppViewSet.as_view({"post": "testsets", "get": "testsets"}),
    ),
    path(
        "api/app/<str:published_uuid>",
        apis.AppViewSet.as_view({"get": "getByPublishedUUID"}),
    ),
    # App Hub
    path("api/appHub", apis.AppHubViewSet.as_view({"get": "list"})),
]
