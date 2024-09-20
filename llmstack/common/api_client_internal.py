from django.test import RequestFactory

from llmstack.connections.apis import ConnectionsViewSet


def get_connections(profile):
    request = RequestFactory().get("/api/connections/")
    request.user = profile.user
    response = ConnectionsViewSet().list(request)
    return dict(map(lambda entry: (entry["id"], entry), response.data))
