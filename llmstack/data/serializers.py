from rest_framework import serializers

from .models import DataSource, DataSourceEntry


class DataSourceSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    owner_email = serializers.SerializerMethodField()
    pipeline = serializers.SerializerMethodField()
    refresh_interval = serializers.SerializerMethodField()
    has_source = serializers.SerializerMethodField()
    is_destination_only = serializers.SerializerMethodField()

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
        return obj.config.get("pipeline", None)

    def get_refresh_interval(self, obj):
        return obj.config.get("refresh_interval", None)

    def get_has_source(self, obj):
        return obj.config.get("pipeline", {}).get("source", {}).get("slug", None) is not None

    def get_is_destination_only(self, obj):
        return (
            obj.config.get("pipeline", {}).get("destination", {}).get("slug", None) is not None
            and self.get_has_source(obj) is False
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
        ]


class DataSourceEntrySerializer(serializers.ModelSerializer):
    datasource = DataSourceSerializer()

    class Meta:
        model = DataSourceEntry
        fields = ["uuid", "datasource", "config", "name", "size", "status", "created_at", "updated_at"]
