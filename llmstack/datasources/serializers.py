import json

from rest_framework import serializers

from .models import DataSource, DataSourceEntry, DataSourceType
from .types import DataSourceTypeFactory


class DataSourceTypeSerializer(serializers.ModelSerializer):
    entry_config_schema = serializers.SerializerMethodField()
    entry_config_ui_schema = serializers.SerializerMethodField()
    sync_config = serializers.SerializerMethodField()

    def get_entry_config_schema(self, obj):
        datasource_type_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
            obj,
        )
        if datasource_type_handler_cls is None:
            return {}
        return json.loads(datasource_type_handler_cls.get_input_schema())

    def get_entry_config_ui_schema(self, obj):
        datasource_type_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
            obj,
        )
        if datasource_type_handler_cls is None:
            return {}
        return datasource_type_handler_cls.get_input_ui_schema()

    def get_sync_config(self, obj):
        datasource_type_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
            obj,
        )
        if datasource_type_handler_cls is None:
            return None
        return datasource_type_handler_cls.get_sync_configuration()

    class Meta:
        model = DataSourceType
        fields = [
            "id",
            "name",
            "description",
            "entry_config_schema",
            "entry_config_ui_schema",
            "sync_config",
            "is_external_datasource",
        ]


class DataSourceSerializer(serializers.ModelSerializer):
    type = DataSourceTypeSerializer()
    owner_email = serializers.SerializerMethodField()

    def get_owner_email(self, obj):
        return obj.owner.email

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
