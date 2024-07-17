from rest_framework import serializers

from .models import DataSource, DataSourceEntry


class DataSourceSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    owner_email = serializers.SerializerMethodField()

    def get_owner_email(self, obj):
        return obj.owner.email

    def get_type(self, obj):
        from llmstack.data.apis import get_data_source_type

        return get_data_source_type(obj.type_slug)

    class Meta:
        model = DataSource
        fields = ["name", "type", "uuid", "size", "created_at", "updated_at", "visibility", "owner_email"]


class DataSourceEntrySerializer(serializers.ModelSerializer):
    datasource = DataSourceSerializer()

    class Meta:
        model = DataSourceEntry
        fields = ["uuid", "datasource", "config", "name", "size", "status", "created_at", "updated_at"]
