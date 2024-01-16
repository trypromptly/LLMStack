from allauth.socialaccount.providers.google.provider import GoogleProvider


class CustomGoogleProvider(GoogleProvider):
    id = 'connection_google'


provider_classes = [CustomGoogleProvider]
