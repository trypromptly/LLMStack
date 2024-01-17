from rest_framework import serializers

from .models import Organization, OrganizationSettings


class OrganizationSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    disabled_api_backends = serializers.SerializerMethodField()
    default_api_backend = serializers.SerializerMethodField()

    def get_logo(self, obj):
        try:
            return OrganizationSettings.objects.get(organization=obj).logo.url
        except BaseException:
            return None

    def get_disabled_api_backends(self, obj):
        return [backend.id for backend in obj.settings.disabled_api_backends.all()]

    def get_default_api_backend(self, obj):
        return obj.settings.default_api_backend.id if obj.settings.default_api_backend else None

    class Meta:
        model = Organization
        fields = [
            "name",
            "logo",
            "slug",
            "disabled_api_backends",
            "default_api_backend",
        ]


class OrganizationSettingsSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="organization.name")
    slug = serializers.CharField(source="organization.slug")
    domains = serializers.ListField(source="organization.domains")
    azure_openai_api_key = serializers.SerializerMethodField()
    openai_key = serializers.SerializerMethodField()
    stabilityai_key = serializers.SerializerMethodField()
    cohere_key = serializers.SerializerMethodField()
    forefrontai_key = serializers.SerializerMethodField()
    elevenlabs_key = serializers.SerializerMethodField()
    anthropic_api_key = serializers.SerializerMethodField()
    aws_secret_access_key = serializers.SerializerMethodField()
    vectorstore_weaviate_api_key = serializers.SerializerMethodField()
    disabled_api_backends = serializers.SerializerMethodField()

    def get_disabled_api_backends(self, obj):
        return [backend.slug for backend in obj.disabled_api_backends.all()]

    def get_azure_openai_api_key(self, obj):
        return obj.decrypt_value(obj.azure_openai_api_key)

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

    def get_anthropic_api_key(self, obj):
        return obj.decrypt_value(obj.anthropic_api_key)

    def get_aws_secret_access_key(self, obj):
        return obj.decrypt_value(obj.aws_secret_access_key)

    def get_vectorstore_weaviate_api_key(self, obj):
        return obj.decrypt_value(obj.vectorstore_weaviate_api_key)

    class Meta:
        model = OrganizationSettings
        fields = [
            "name",
            "slug",
            "domains",
            "logo",
            "disabled_api_backends",
            "default_app_visibility",
            "max_app_visibility",
            "allow_user_keys",
            "azure_openai_api_key",
            "openai_key",
            "stabilityai_key",
            "cohere_key",
            "forefrontai_key",
            "elevenlabs_key",
            "azure_openai_endpoint",
            "anthropic_api_key",
            "aws_access_key_id",
            "aws_secret_access_key",
            "aws_default_region",
            "vectorstore_weaviate_url",
            "vectorstore_weaviate_api_key",
            "vectorstore_weaviate_text2vec_openai_module_config",
            "use_own_vectorstore",
            "use_azure_openai_embeddings",
            "embeddings_api_rate_limit",
            "default_api_backend",
        ]
