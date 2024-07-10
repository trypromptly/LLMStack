from rest_framework import serializers

from .models import DataSource, DataSourceEntry
from .types import DataSourceTypeFactory


class DataSourceSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    owner_email = serializers.SerializerMethodField()

    def get_owner_email(self, obj):
        return obj.owner.email

    def get_type(self, obj):
        from llmstack.datasources.apis import get_data_source_type

        return get_data_source_type(obj.type_slug)

    class Meta:
        model = DataSource
        fields = [
            "name",
            "type",
            "uuid",
            "size",
            "created_at",
            "updated_at",
            "visibility",
            "owner_email",
        ]


class DataSourceEntrySerializer(serializers.ModelSerializer):
    datasource = DataSourceSerializer()
    sync_config = serializers.SerializerMethodField()

    def get_sync_config(self, obj):
        datasource_type_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
            obj.datasource.type,
        )
        if datasource_type_handler_cls is None:
            return None
        if "input" not in obj.config:
            return None

        return datasource_type_handler_cls.get_sync_configuration()

    class Meta:
        model = DataSourceEntry
        fields = [
            "uuid",
            "datasource",
            "config",
            "name",
            "size",
            "status",
            "created_at",
            "updated_at",
            "sync_config",
        ]
