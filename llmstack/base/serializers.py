from rest_framework import serializers

from llmstack.base.models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email")
    name = serializers.SerializerMethodField()
    username = serializers.CharField(source="user.username")
    openai_key = serializers.SerializerMethodField()
    stabilityai_key = serializers.SerializerMethodField()
    cohere_key = serializers.SerializerMethodField()
    forefrontai_key = serializers.SerializerMethodField()
    elevenlabs_key = serializers.SerializerMethodField()
    google_service_account_json_key = serializers.SerializerMethodField()
    azure_openai_api_key = serializers.SerializerMethodField()
    localai_api_key = serializers.SerializerMethodField()
    localai_base_url = serializers.SerializerMethodField()
    anthropic_api_key = serializers.SerializerMethodField()

    avatar = serializers.SerializerMethodField()

    def get_openai_key(self, obj):
        return obj.decrypt_value(obj.openai_key)

    def get_stabilityai_key(self, obj):
        return obj.decrypt_value(obj.stabilityai_key)

    def get_cohere_key(self, obj):
        return obj.decrypt_value(obj.cohere_key)

    def get_forefrontai_key(self, obj):
        return obj.decrypt_value(obj.forefrontai_key)

    def get_elevenlabs_key(self, obj):
        return obj.decrypt_value(obj.elevenlabs_key)

    def get_google_service_account_json_key(self, obj):
        return obj.decrypt_value(obj.google_service_account_json_key)

    def get_azure_openai_api_key(self, obj):
        return obj.decrypt_value(obj.azure_openai_api_key)

    def get_localai_api_key(self, obj):
        return obj.decrypt_value(obj.localai_api_key)

    def get_localai_base_url(self, obj):
        return obj.localai_base_url

    def get_anthropic_api_key(self, obj):
        return obj.decrypt_value(obj.anthropic_api_key)

    def get_avatar(self, obj):
        return obj.user.socialaccount_set.first().get_avatar_url() if obj.user.socialaccount_set.first() else None

    def get_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    class Meta:
        model = Profile
        fields = [
            "name",
            "user_email",
            "username",
            "token",
            "openai_key",
            "stabilityai_key",
            "cohere_key",
            "forefrontai_key",
            "elevenlabs_key",
            "google_service_account_json_key",
            "azure_openai_api_key",
            "localai_api_key",
            "localai_base_url",
            "anthropic_api_key",
            "logo",
            "organization",
            "avatar",
        ]
