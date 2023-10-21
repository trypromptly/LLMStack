from django.urls import path
from .apis import ConnectionsViewSet

urlpatterns = [
    path('api/connection_types',
         ConnectionsViewSet.as_view({'get': 'get_connection_types'})),

    path('api/connections', ConnectionsViewSet.as_view({'get': 'list'})),

    path(
        'api/connections/<str:uid>',
        ConnectionsViewSet.as_view(
            {'get': 'get', 'post': 'post', 'patch': 'patch', 'delete': 'delete'}),
    ),
]
