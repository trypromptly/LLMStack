from django.urls import path

from . import apis

urlpatterns = [
    # Data Types
    path(
        "api/datasource_types",
        apis.DataSourceTypeViewSet.as_view({"get": "list"}),
    ),
    path(
        "api/datasource_types/<str:slug>",
        apis.DataSourceTypeViewSet.as_view({"get": "get"}),
    ),
    # Data sources
    path(
        "api/datasources",
        apis.DataSourceViewSet.as_view(
            {"get": "get", "post": "post", "put": "put"},
        ),
    ),
    path(
        "api/datasources/url/extract_urls",
        apis.DataSourceViewSet.as_view({"post": "extract_urls"}),
    ),
    path(
        "api/datasources/<str:uid>",
        apis.DataSourceViewSet.as_view({"get": "get", "delete": "delete"}),
    ),
    path(
        "api/datasources/<str:uid>/entries",
        apis.DataSourceViewSet.as_view({"get": "getEntries"}),
    ),
    path(
        "api/datasources/<str:uid>/add_entry",
        apis.DataSourceViewSet.as_view({"post": "add_entry"}),
    ),
    path(
        "api/datasources/<str:uid>/add_entry_async",
        apis.DataSourceViewSet.as_view({"post": "add_entry_async"}),
    ),
    path(
        "api/datasources/<str:uid>/add_entry_jobs",
        apis.DataSourceViewSet.as_view({"get": "add_entry_jobs"}),
    ),
    # Data source entries
    path(
        "api/datasource_entries",
        apis.DataSourceEntryViewSet.as_view({"get": "get"}),
    ),
    path(
        "api/datasource_entries/upsert",
        apis.DataSourceEntryViewSet.as_view({"post": "upsert"}),
    ),
    path(
        "api/datasource_entries/<str:uid>",
        apis.DataSourceEntryViewSet.as_view(
            {"get": "get", "delete": "delete"},
        ),
    ),
    path(
        "api/datasource_entries/<str:uid>/text_content",
        apis.DataSourceEntryViewSet.as_view({"get": "text_content"}),
    ),
    path(
        "api/datasource_entries/<str:uid>/resync",
        apis.DataSourceEntryViewSet.as_view({"post": "resync"}),
    ),
]
