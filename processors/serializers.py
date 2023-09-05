import json

from rest_framework import serializers

from .models import ApiBackend
from .models import ApiProvider
from .models import Endpoint
from .models import PromptHub
from .models import Request
from .models import Response
from .models import RunEntry
from .models import Share
from .models import ShareTag
from apps.models import App
from apps.models import AppSession
from processors.providers.api_processors import ApiProcessorFactory


class ApiProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiProvider
        fields = ['name', 'prefix', 'slug']


class ApiBackendSerializer(serializers.ModelSerializer):
    api_provider = ApiProviderSerializer()
    config_schema = serializers.SerializerMethodField()
    input_schema = serializers.SerializerMethodField()
    output_schema = serializers.SerializerMethodField()
    config_ui_schema = serializers.SerializerMethodField()
    input_ui_schema = serializers.SerializerMethodField()
    output_ui_schema = serializers.SerializerMethodField()

    def get_config_schema(self, obj):
        processor_cls = ApiProcessorFactory.get_api_processor(
            obj.slug, obj.api_provider.slug)
        if processor_cls is None:
            return {}
        return json.loads(processor_cls.get_configuration_schema())

    def get_input_schema(self, obj):
        processor_cls = ApiProcessorFactory.get_api_processor(
            obj.slug, obj.api_provider.slug)
        if processor_cls is None:
            return {}
        return json.loads(processor_cls.get_input_schema())

    def get_output_schema(self, obj):
        processor_cls = ApiProcessorFactory.get_api_processor(
            obj.slug, obj.api_provider.slug)
        if processor_cls is None:
            return {}
        return json.loads(processor_cls.get_output_schema())

    def get_config_ui_schema(self, obj):
        processor_cls = ApiProcessorFactory.get_api_processor(
            obj.slug, obj.api_provider.slug)
        if processor_cls is None:
            return {}
        return processor_cls.get_configuration_ui_schema()

    def get_input_ui_schema(self, obj):
        processor_cls = ApiProcessorFactory.get_api_processor(
            obj.slug, obj.api_provider.slug)
        if processor_cls is None:
            return {}
        return processor_cls.get_input_ui_schema()

    def get_output_ui_schema(self, obj):
        processor_cls = ApiProcessorFactory.get_api_processor(
            obj.slug, obj.api_provider.slug)
        if processor_cls is None:
            return {}
        return processor_cls.get_output_ui_schema()

    class Meta:
        model = ApiBackend
        fields = [
            'id', 'name', 'slug', 'api_provider', 'api_endpoint', 'params', 'description', 'input_schema',
            'output_schema', 'config_schema', 'config_ui_schema', 'input_ui_schema', 'output_ui_schema',
        ]


class EndpointSerializer(serializers.ModelSerializer):
    api_backend = ApiBackendSerializer()

    class Meta:
        model = Endpoint
        fields = [
            'name', 'uuid', 'api_backend', 'param_values', 'post_processor', 'prompt', 'draft',
            'is_live', 'parent_uuid', 'description', 'version', 'created_on', 'is_app', 'config', 'input',
        ]


class RequestSerializer(serializers.ModelSerializer):
    endpoint = EndpointSerializer()

    class Meta:
        model = Request
        fields = [
            'endpoint', 'input', 'param_values',
            'prompt_values', 'created_on',
        ]


class ResponseSerializer(serializers.ModelSerializer):
    request = RequestSerializer()

    class Meta:
        model = Response
        fields = [
            'request', 'raw_response',
            'processed_response', 'response_code', 'created_on',
        ]


class HistorySerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if self.context.get('hide_details'):
            representation.pop('request_body', None)
            representation.pop('request_headers', None)
            representation.pop('request_content_type', None)
            representation.pop('response_body', None)
            representation.pop('response_headers', None)
            representation.pop('response_content_type', None)
            representation.pop('processor_runs', None)

        return representation

    class Meta:
        model = RunEntry
        fields = [
            'request_uuid', 'app_uuid', 'endpoint_uuid', 'session_key', 'created_at', 'request_user_email',
            'request_ip', 'request_location', 'request_user_agent', 'request_content_type', 'request_body',
            'response_status', 'response_body', 'response_content_type', 'response_headers', 'response_time',
            'processor_runs', 'platform_data',
        ]


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
