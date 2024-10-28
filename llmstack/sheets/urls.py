from django.urls import path

from llmstack.sheets.apis import PromptlySheetTemplateViewSet, PromptlySheetViewSet

urlpatterns = [
    path(
        "api/sheets/data_transformation/generate",
        PromptlySheetViewSet.as_view({"post": "generate_data_transformation_template"}),
    ),
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
        "api/sheets/<str:sheet_uuid>/runs",
        PromptlySheetViewSet.as_view({"get": "list_runs"}),
    ),
    path(
        "api/sheets/<str:sheet_uuid>/download",
        PromptlySheetViewSet.as_view({"get": "download"}),
    ),
    path(
        "api/sheets/<str:sheet_uuid>/upload_assets",
        PromptlySheetViewSet.as_view({"post": "upload_sheet_assets"}),
    ),
    path(
        "api/sheets/<str:sheet_uuid>/runs/<str:run_id>/download",
        PromptlySheetViewSet.as_view({"get": "download_run"}),
    ),
    path(
        "api/sheets/<str:sheet_uuid>/runs/<str:run_id>/cancel",
        PromptlySheetViewSet.as_view({"post": "cancel_run"}),
    ),
]
