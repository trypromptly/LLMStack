from django.urls import path

from llmstack.promptly_sheets.apis import PromptlySheetCellViewSet, PromptlySheetViewSet

urlpatterns = [
    path("api/sheets", PromptlySheetViewSet.as_view({"get": "list", "post": "create"})),
    path(
        "api/sheets/<str:sheet_uuid>",
        PromptlySheetViewSet.as_view({"get": "list", "patch": "patch", "delete": "delete"}),
    ),
    path(
        "api/sheets/<str:sheet_uuid>/execute",
        PromptlySheetViewSet.as_view({"post": "execute"}),
    ),
    path(
        "api/sheets/<str:sheet_uuid>/cells",
        PromptlySheetCellViewSet.as_view({"get": "list", "post": "create"}),
    ),
    path(
        "api/sheets/<str:sheet_uuid>/cells/<str:cell_uuid>",
        PromptlySheetCellViewSet.as_view({"get": "list", "patch": "patch", "delete": "delete"}),
    ),
    path(
        "api/sheets/<str:sheet_uuid>/cells/<str:cell_uuid>/execute",
        PromptlySheetCellViewSet.as_view({"post": "execute"}),
    ),
]
