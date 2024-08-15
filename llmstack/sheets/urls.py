from django.urls import path

from llmstack.promptly_sheets.apis import PromptlySheetViewSet

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
        "api/sheets/<str:sheet_uuid>/execute_async",
        PromptlySheetViewSet.as_view({"post": "execute_async"}),
    ),
]
