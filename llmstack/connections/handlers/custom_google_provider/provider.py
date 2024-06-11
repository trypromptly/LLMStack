from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.providers.google.provider import GoogleProvider


class CustomGoogleProvider(GoogleProvider):
    id = "connection_google"
    name = "Connection Google"

    def get_app(self, request, config=None):
        adapter = get_adapter(request)
        return adapter.get_app(request, self.id)


provider_classes = [CustomGoogleProvider]
