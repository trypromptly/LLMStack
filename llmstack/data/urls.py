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
    path(
        "api/data/pipeline/sources",
        apis.PipelineViewSet.as_view({"get": "sources"}),
    ),
    path(
        "api/data/pipeline/destinations",
        apis.PipelineViewSet.as_view({"get": "destinations"}),
    ),
    path(
        "api/data/pipeline/transformations",
        apis.PipelineViewSet.as_view({"get": "transformations"}),
    ),
    path(
        "api/data/pipeline/embeddings",
        apis.PipelineViewSet.as_view({"get": "embeddings"}),
    ),
    path(
        "api/data/pipeline/templates",
        apis.PipelineViewSet.as_view({"get": "templates"}),
    ),
    # Data sources
    path(
        "api/datasources",
        apis.DataSourceViewSet.as_view({"get": "get", "post": "post"}),
    ),
    path(
        "api/datasources/url/extract_urls",
        apis.DataSourceViewSet.as_view({"post": "extract_urls"}),
    ),
    path(
        "api/datasources/<str:uid>",
        apis.DataSourceViewSet.as_view({"get": "get", "delete": "delete", "patch": "patch"}),
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
    path(
        "api/datasource_entries/<str:uid>/resync_async",
        apis.DataSourceEntryViewSet.as_view({"post": "resync_async"}),
    ),
]
