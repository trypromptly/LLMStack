from rest_framework import serializers

from llmstack.apps.models import App

from .models import AppStoreApp


class AppStoreAppSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        context = kwargs.pop("context", None)
        request = context.get("request") if context else None

        include_data = request and request.query_params.get("include_data", "false").lower() == "true"

        # Check the include_data flag in context if request doesn't have it
        if not include_data and context:
            include_data = context.get("include_data", False)

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        if not include_data:
            self.fields.pop("data")

    data = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    icon = serializers.SerializerMethodField()
    icon128 = serializers.SerializerMethodField()
    icon512 = serializers.SerializerMethodField()

    class AppSerializer(serializers.ModelSerializer):
        class Meta:
            model = App
            fields = ["config", "input_schema", "input_ui_schema", "output_template"]

    def get_data(self, obj):
        app_data = obj.app_data
        if app_data:
            if app_data["icon"]:
                app_data["icon"] = obj.icon256_url if obj.icon256 else obj.icon_url

            return app_data

        return None

    def get_username(self, obj):
        return "admin"

    def get_icon(self, obj):
        return obj.icon_url if obj.icon else None

    def get_icon128(self, obj):
        return obj.icon128_url if obj.icon128 else None

    def get_icon512(self, obj):
        return obj.icon512_url if obj.icon512 else None

    class Meta:
        model = AppStoreApp
        fields = [
            "uuid",
            "username",
            "version",
            "name",
            "slug",
            "description",
            "categories",
            "data",
            "created_at",
            "icon",
            "icon128",
            "icon512",
        ]
