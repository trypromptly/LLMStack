import json
from functools import cache

from rest_framework import serializers

from llmstack.processors.providers.api_processors import ApiProcessorFactory

from .models import ApiBackend, ApiProvider, Endpoint, Request, Response, RunEntry


class ApiProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiProvider
        fields = ["name", "prefix", "slug"]


class ApiBackendSerializer(serializers.ModelSerializer):
    api_provider = ApiProviderSerializer()
    config_schema = serializers.SerializerMethodField()
    input_schema = serializers.SerializerMethodField()
    output_schema = serializers.SerializerMethodField()
    config_ui_schema = serializers.SerializerMethodField()
    input_ui_schema = serializers.SerializerMethodField()
    output_ui_schema = serializers.SerializerMethodField()
    output_template = serializers.SerializerMethodField()

    def get_config_schema(self, obj):
        processor_cls = ApiProcessorFactory.get_api_processor(
            obj.slug,
            obj.api_provider.slug,
        )
        if processor_cls is None:
            return {}
        return json.loads(processor_cls.get_configuration_schema())

    def get_input_schema(self, obj):
        processor_cls = ApiProcessorFactory.get_api_processor(
            obj.slug,
            obj.api_provider.slug,
        )
        if processor_cls is None:
            return {}
        return json.loads(processor_cls.get_input_schema())

    def get_output_schema(self, obj):
        processor_cls = ApiProcessorFactory.get_api_processor(
            obj.slug,
            obj.api_provider.slug,
        )
        if processor_cls is None:
            return {}
        return json.loads(processor_cls.get_output_schema())

    def get_config_ui_schema(self, obj):
        processor_cls = ApiProcessorFactory.get_api_processor(
            obj.slug,
            obj.api_provider.slug,
        )
        if processor_cls is None:
            return {}
        return processor_cls.get_configuration_ui_schema()

    def get_input_ui_schema(self, obj):
        processor_cls = ApiProcessorFactory.get_api_processor(
            obj.slug,
            obj.api_provider.slug,
        )
        if processor_cls is None:
            return {}
        return processor_cls.get_input_ui_schema()

    def get_output_ui_schema(self, obj):
        processor_cls = ApiProcessorFactory.get_api_processor(
            obj.slug,
            obj.api_provider.slug,
        )
        if processor_cls is None:
            return {}
        return processor_cls.get_output_ui_schema()

    def get_output_template(self, obj):
        processor_cls = ApiProcessorFactory.get_api_processor(
            obj.slug,
            obj.api_provider.slug,
        )
        if processor_cls is None:
            return None
        return processor_cls.get_output_template().model_dump() if processor_cls.get_output_template() else None

    class Meta:
        model = ApiBackend
        fields = [
            "id",
            "name",
            "slug",
            "api_provider",
            "api_endpoint",
            "params",
            "description",
            "input_schema",
            "output_schema",
            "config_schema",
            "config_ui_schema",
            "input_ui_schema",
            "output_ui_schema",
            "output_template",
        ]


class EndpointSerializer(serializers.ModelSerializer):
    api_backend = ApiBackendSerializer()

    class Meta:
        model = Endpoint
        fields = [
            "name",
            "uuid",
            "api_backend",
            "param_values",
            "post_processor",
            "prompt",
            "draft",
            "is_live",
            "parent_uuid",
            "description",
            "version",
            "created_on",
            "is_app",
            "config",
            "input",
        ]


class RequestSerializer(serializers.ModelSerializer):
    endpoint = EndpointSerializer()

    class Meta:
        model = Request
        fields = [
            "endpoint",
            "input",
            "param_values",
            "prompt_values",
            "created_on",
        ]


class ResponseSerializer(serializers.ModelSerializer):
    request = RequestSerializer()

    class Meta:
        model = Response
        fields = [
            "request",
            "raw_response",
            "processed_response",
            "response_code",
            "created_on",
        ]


class HistorySerializer(serializers.ModelSerializer):
    app_detail = serializers.SerializerMethodField()
    processor_runs = serializers.SerializerMethodField()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if self.context.get("hide_details"):
            representation.pop("request_body", None)
            representation.pop("request_headers", None)
            representation.pop("request_content_type", None)
            representation.pop("response_body", None)
            representation.pop("response_headers", None)
            representation.pop("response_content_type", None)
            representation.pop("processor_runs", None)

        return representation

    @cache
    def get_app_detail(self, obj):
        from llmstack.apps.models import App

        def get_app_store_app(uuid):
            try:
                from promptly_app_store.models import AppStoreApp
            except ImportError:
                from llmstack.app_store.models import AppStoreApp
            return AppStoreApp.objects.filter(uuid=uuid).first()

        if obj.app_store_uuid:
            app = get_app_store_app(obj.app_store_uuid)
            if not app:
                return {"name": "Deleted App", "path": "/"}
            return {"name": app.name, "path": f"/a/{app.slug}"}

        if obj.app_uuid:
            app = App.objects.filter(uuid=obj.app_uuid).first()
            if app:
                return {"name": app.name, "path": f"/apps/{obj.app_uuid}"}
            if obj.request_body:
                try:
                    body = json.loads(json.dumps(obj.request_body))
                    if "config" in body:
                        return {"name": "Playground", "path": "/playground"}
                except Exception:
                    pass
        return {"name": "Deleted App", "path": "/"}

    def get_processor_runs(self, obj):
        if obj.processor_runs_objref:
            try:
                return obj.get_processor_runs_from_objref()
            except Exception:
                pass

        return []

    class Meta:
        model = RunEntry
        fields = [
            "request_uuid",
            "app_uuid",
            "app_detail",
            "app_store_uuid",
            "endpoint_uuid",
            "session_key",
            "created_at",
            "request_user_email",
            "request_ip",
            "request_location",
            "request_user_agent",
            "request_content_type",
            "request_body",
            "response_status",
            "response_body",
            "response_content_type",
            "response_headers",
            "response_time",
            "processor_runs",
            "platform_data",
        ]


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
