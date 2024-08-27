from django.urls import path

from llmstack.sheets.apis import PromptlySheetTemplateViewSet, PromptlySheetViewSet

urlpatterns = [
    path("api/sheets/templates", PromptlySheetTemplateViewSet.as_view({"get": "list_templates"})),
    path("api/sheets/templates/<str:slug>", PromptlySheetTemplateViewSet.as_view({"get": "list_templates"})),
    path("api/sheets", PromptlySheetViewSet.as_view({"get": "list", "post": "create"})),
    path(
        "api/sheets/<str:sheet_uuid>",
        PromptlySheetViewSet.as_view({"get": "list", "patch": "patch", "delete": "delete"}),
    ),
    path(
        "api/sheets/<str:sheet_uuid>/run",
        PromptlySheetViewSet.as_view({"post": "run_async"}),
    ),
    path(
        "api/sheets/<str:sheet_uuid>/download",
        PromptlySheetViewSet.as_view({"get": "download"}),
    ),
    path(
        "api/sheets/<str:sheet_uuid>/<str:run_id>/download",
        PromptlySheetViewSet.as_view({"get": "download_run"}),
    ),
]
