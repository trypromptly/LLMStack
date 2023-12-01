from allauth.socialaccount.providers.google.provider import GoogleProvider

class CustomGoogleProvider(GoogleProvider):
    id = 'custom_google'

provider_classes = [CustomGoogleProvider]
