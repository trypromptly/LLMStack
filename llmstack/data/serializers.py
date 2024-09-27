from rest_framework import serializers

from .models import DataSource, DataSourceAccessPermission, DataSourceEntry


class DataSourceSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    owner_email = serializers.SerializerMethodField()
    pipeline = serializers.SerializerMethodField()
    refresh_interval = serializers.SerializerMethodField()
    has_source = serializers.SerializerMethodField()
    is_destination_only = serializers.SerializerMethodField()
    has_read_permission = serializers.SerializerMethodField()
    has_write_permission = serializers.SerializerMethodField()
    is_user_owned = serializers.SerializerMethodField()
    access_permission = serializers.SerializerMethodField()

    def get_owner_email(self, obj):
        return obj.owner.email

    def get_type(self, obj):
        if obj.type_slug:
            return {
                "slug": obj.type_slug,
                "name": obj.type_slug,
            }
        else:
            return {
                "slug": "custom",
                "name": "Custom",
            }

    def get_pipeline(self, obj):
        config = obj.config or {}
        pipeline = config.get("pipeline", None)
        if pipeline and "source" in pipeline and pipeline["source"] and "data" in pipeline["source"]:
            pipeline["source"]["data"] = {}

        return pipeline

    def get_refresh_interval(self, obj):
        config = obj.config or {}
        return config.get("refresh_interval", None)

    def get_has_source(self, obj):
        config = obj.config or {}
        source = config.get("pipeline", {}).get("source", {}) or {}
        return source.get("slug", None) is not None

    def get_is_destination_only(self, obj):
        config = obj.config or {}
        destination = config.get("pipeline", {}).get("destination", {}) or {}
        return destination.get("slug", None) is not None and self.get_has_source(obj) is False

    def get_has_read_permission(self, obj):
        return obj.has_read_permission(self.context.get("request_user"))

    def get_has_write_permission(self, obj):
        return obj.has_write_permission(self.context.get("request_user"))

    def get_is_user_owned(self, obj):
        return obj.owner == self.context.get("request_user")

    def get_access_permission(self, obj):
        return (
            DataSourceAccessPermission.WRITE if self.get_has_write_permission(obj) else DataSourceAccessPermission.READ
        )

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
            "pipeline",
            "refresh_interval",
            "has_source",
            "is_destination_only",
            "has_read_permission",
            "has_write_permission",
            "is_user_owned",
            "access_permission",
        ]


class DataSourceEntrySerializer(serializers.ModelSerializer):
    datasource = DataSourceSerializer()
    config = serializers.SerializerMethodField()

    def get_config(self, obj):
        config = obj.config or {}
        config.pop("input", None)

        return config

    class Meta:
        model = DataSourceEntry
        fields = ["uuid", "datasource", "config", "name", "size", "status", "created_at", "updated_at"]
