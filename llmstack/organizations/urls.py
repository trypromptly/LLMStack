from django.urls import path

from . import apis

urlpatterns = [
    # APIs
    path('api/org', apis.OrganizationViewSet.as_view({'get': 'get'})),
    path(
        'api/org/settings',
        apis.OrganizationSettingsViewSet.as_view({'get': 'get'}),
    ),
    path(
        'api/org/members',
        apis.OrganizationMembersViewSet.as_view({'get': 'get'}),
    ),
    path(
        'api/org/apps',
        apis.OrganizationAppsViewSet.as_view({'get': 'get'}),
    ),

    # Data sources
    path(
        'api/org/datasources',
        apis.OrganizationDataSourceViewSet.as_view({'get': 'get'}),
    ),
    path(
        'api/org/datasources/<str:uid>',
        apis.OrganizationDataSourceViewSet.as_view({'get': 'get', 'delete': 'delete'}),
    ),
    path(
        'api/org/datasources/<str:uid>/entries',
        apis.OrganizationDataSourceViewSet.as_view({'get': 'getEntries'}),
    ),
    path(
        'api/org/datasources/<str:uid>/add_entry',
        apis.OrganizationDataSourceViewSet.as_view({'post': 'add_entry'}),
    ),

    # Data source entries
    path(
        'api/org/datasource_entries',
        apis.OrganizationDataSourceEntryViewSet.as_view({'get': 'get'}),
    ),
    path(
        'api/org/datasource_entries/<str:uid>',
        apis.OrganizationDataSourceEntryViewSet.as_view({'get': 'get'}),
    ),
    path(
        'api/org/datasource_entries/<str:uid>/text_content',
        apis.OrganizationDataSourceEntryViewSet.as_view({'get': 'text_content'}),
    ),
]
