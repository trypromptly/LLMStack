from django.urls import path

from . import apis

urlpatterns = [
    # APIs

    # Authentication
    path('api/login', apis.LoginView.as_view()),
    path('api/logout', apis.LogoutAPIView.as_view()),

    # Backends
    path(
        'api/apibackends/',
        apis.ApiBackendViewSet.as_view({'get': 'filtered'}),
    ),
    path('api/apibackends', apis.ApiBackendViewSet.as_view({'get': 'list'})),
    path('api/apiproviders', apis.ApiProviderViewSet.as_view({'get': 'list'})),

    # Endpoints
    path(
        'api/endpoints/invoke_api/<str:id>',
        apis.EndpointViewSet.as_view({'post': 'invoke_api'}),
    ),
    path(
        'api/endpoints/invoke_api/<str:id>/<str:version>',
        apis.EndpointViewSet.as_view({'post': 'invoke_api'}),
    ),
    path(
        'api/endpoints/<str:id>', apis.EndpointViewSet.as_view(
            {'put': 'update', 'get': 'get', 'post': 'invoke_api', 'delete': 'delete'},
        ),
    ),
    path(
        'api/endpoints/<str:id>/<str:version>',
        apis.EndpointViewSet.as_view({'post': 'invoke_api'}),
    ),

    path(
        'api/endpoints', apis.EndpointViewSet.as_view(
            {'get': 'list', 'post': 'create', 'patch': 'patch'},
        ),
    ),
    # Playground
    path('api/playground/run', apis.EndpointViewSet.as_view({'post': 'run'})),

    # History
    path('api/history', apis.HistoryViewSet.as_view({'get': 'list'})),
    path(
        'api/history/sessions',
        apis.HistoryViewSet.as_view({'get': 'list_sessions'}),
    ),
    path(
        'api/history/<str:request_uuid>',
        apis.HistoryViewSet.as_view({'get': 'get'}),
    ),
]
