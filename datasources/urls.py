from django.urls import path

from . import apis

urlpatterns = [
    # Data Types
    path(
        'api/datasource_types',
        apis.DataSourceTypeViewSet.as_view({'get': 'get'}),
    ),
    path(
        'api/datasource_types',
        apis.DataSourceTypeViewSet.as_view({'get': 'get'}),
    ),

    # Data sources
    path(
        'api/datasources',
        apis.DataSourceViewSet.as_view({'get': 'get', 'post': 'post'}),
    ),
    path(
        'api/datasources/url/extract_urls',
        apis.DataSourceViewSet.as_view({'post': 'extract_urls'}),
    ),
    path(
        'api/datasources/<str:uid>',
        apis.DataSourceViewSet.as_view({'get': 'get', 'delete': 'delete'}),
    ),
    path(
        'api/datasources/<str:uid>/entries',
        apis.DataSourceViewSet.as_view({'get': 'getEntries'}),
    ),
    path(
        'api/datasources/<str:uid>/add_entry',
        apis.DataSourceViewSet.as_view({'post': 'add_entry'}),
    ),

    # Data source entries
    path(
        'api/datasource_entries',
        apis.DataSourceEntryViewSet.as_view({'get': 'get'}),
    ),
    path(
        'api/datasource_entries/<str:uid>',
        apis.DataSourceEntryViewSet.as_view({'get': 'get', 'delete': 'delete'}),
    ),
    path(
        'api/datasource_entries/<str:uid>/text_content',
        apis.DataSourceEntryViewSet.as_view({'get': 'text_content'}),
    ),
]
