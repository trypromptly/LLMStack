from rest_framework import serializers

from .models import DataSource
from .models import DataSourceEntry
from .models import DataSourceType
from .types import DataSourceTypeFactory


class DataSourceTypeSerializer(serializers.ModelSerializer):
    entry_config_schema = serializers.SerializerMethodField()
    entry_config_ui_schema = serializers.SerializerMethodField()

    def get_entry_config_schema(self, obj):
        datasource_type_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
            obj,
        )
        if datasource_type_handler_cls is None:
            return {}
        return datasource_type_handler_cls.get_entry_config_schema()

    def get_entry_config_ui_schema(self, obj):
        datasource_type_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
            obj,
        )
        if datasource_type_handler_cls is None:
            return {}
        return datasource_type_handler_cls.get_entry_config_ui_schema()

    class Meta:
        model = DataSourceType
        fields = [
            'id', 'name', 'description',
            'entry_config_schema', 'entry_config_ui_schema',
        ]


class DataSourceSerializer(serializers.ModelSerializer):
    type = DataSourceTypeSerializer()
    owner_email = serializers.SerializerMethodField()

    def get_owner_email(self, obj):
        return obj.owner.email

    class Meta:
        model = DataSource
        fields = [
            'name', 'type', 'uuid', 'size',
            'created_at', 'updated_at', 'visibility', 'owner_email',
        ]


class DataSourceEntrySerializer(serializers.ModelSerializer):
    datasource = DataSourceSerializer()

    class Meta:
        model = DataSourceEntry
        fields = [
            'uuid', 'datasource', 'config',
            'name', 'size', 'status', 'created_at', 'updated_at',
        ]
