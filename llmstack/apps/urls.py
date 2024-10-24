from django.urls import path

from llmstack.apps.apis import (
    AppViewSet,
    DiscordViewSet,
    SlackViewSet,
    TwilioSMSViewSet,
)

urlpatterns = [
    # Apps
    path(
        "api/apps/templates",
        AppViewSet.as_view({"get": "getTemplates"}),
    ),
    path(
        "api/apps/templates/<str:slug>",
        AppViewSet.as_view({"get": "getTemplates"}),
    ),
    path("api/apps", AppViewSet.as_view({"get": "get", "post": "post"})),
    path("api/apps/shared", AppViewSet.as_view({"get": "getShared"})),
    path(
        "api/apps/<str:uid>",
        AppViewSet.as_view(
            {"get": "get", "patch": "patch", "delete": "delete"},
        ),
    ),
    path(
        "api/apps/<str:uid>/processors/<str:id>/run",
        AppViewSet.as_view({"post": "processor_run"}),
    ),
    path("api/apps/<str:uid>/run", AppViewSet.as_view({"post": "run"})),
    path(
        "api/apps/<str:uid>/versions",
        AppViewSet.as_view({"get": "versions"}),
    ),
    path(
        "api/apps/<str:uid>/versions/<str:version>",
        AppViewSet.as_view({"get": "versions"}),
    ),
    path(
        "api/apps/<str:uid>/discord/run",
        DiscordViewSet.as_view({"post": "run_async"}),
    ),
    path(
        "api/apps/<str:uid>/slack/run",
        SlackViewSet.as_view({"post": "run_async"}),
    ),
    path(
        "api/apps/<str:uid>/twiliosms/run",
        TwilioSMSViewSet.as_view({"post": "run_async"}),
    ),
    path(
        "api/apps/<str:uid>/run/<str:session_id>",
        AppViewSet.as_view({"post": "run"}),
    ),
    path(
        "api/apps/<str:uid>/publish",
        AppViewSet.as_view({"post": "publish"}),
    ),
    path(
        "api/apps/<str:uid>/unpublish",
        AppViewSet.as_view({"post": "unpublish"}),
    ),
    path(
        "api/app/<str:published_uuid>",
        AppViewSet.as_view({"get": "getByPublishedUUID"}),
    ),
]
