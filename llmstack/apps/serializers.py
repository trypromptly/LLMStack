from rest_framework import serializers

from llmstack.apps.yaml_loader import get_app_template_by_slug

from .models import App, AppAccessPermission, AppData
from .models import AppHub
from .models import AppRunGraphEntry
from .models import AppSession
from .models import AppTemplate
from .models import AppTemplateCategory
from .models import AppType
from .models import TestCase
from .models import TestSet
from llmstack.apps.app_templates import AppTemplateFactory
from llmstack.apps.app_types import AppTypeFactory
from play.utils import convert_template_vars_from_legacy_format
from processors.models import ApiBackend
from processors.models import Endpoint
from base.models import Profile
from processors.serializers import ApiBackendSerializer
from processors.serializers import ApiProviderSerializer
from processors.serializers import EndpointSerializer


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)
        self._request_user = kwargs.pop('request_user', None)

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class AppTypeSerializer(serializers.ModelSerializer):
    config_schema = serializers.SerializerMethodField()
    config_ui_schema = serializers.SerializerMethodField()

    def get_config_schema(self, obj):
        app_type_handler_cls = AppTypeFactory.get_app_type_handler(obj)
        if app_type_handler_cls is None:
            return {}
        return app_type_handler_cls.get_config_schema()

    def get_config_ui_schema(self, obj):
        app_type_handler_cls = AppTypeFactory.get_app_type_handler(obj)
        if app_type_handler_cls is None:
            return {}
        return app_type_handler_cls.get_config_ui_schema()

    class Meta:
        model = AppType
        fields = [
            'id', 'slug', 'name', 'description',
            'config_schema', 'config_ui_schema',
        ]


class AppRunGraphEntrySerializer(serializers.ModelSerializer):
    entry_endpoint = EndpointSerializer()
    exit_endpoint = EndpointSerializer()

    class Meta:
        model = AppRunGraphEntry
        fields = ['id', 'entry_endpoint', 'exit_endpoint', 'data_transformer']


class AppSerializer(DynamicFieldsModelSerializer):

    class AppProcessorEndpointSerializer(serializers.ModelSerializer):
        class AppProcessorEndpointApiBackendSerializer(serializers.ModelSerializer):
            api_provider = ApiProviderSerializer()

            class Meta:
                model = ApiBackend
                fields = ['id', 'name', 'api_provider']

        api_backend = AppProcessorEndpointApiBackendSerializer()

        class Meta:
            model = Endpoint
            fields = ['name', 'uuid', 'api_backend', 'description']

    class AppTemplateSerializer(serializers.ModelSerializer):
        class Meta:
            model = AppTemplate
            fields = ['name', 'slug']

    type = AppTypeSerializer()
    data = serializers.SerializerMethodField()
    processors = serializers.SerializerMethodField()
    unique_processors = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()
    is_shareable = serializers.SerializerMethodField()
    has_footer = serializers.SerializerMethodField()
    last_modified_by_email = serializers.SerializerMethodField()
    owner_email = serializers.SerializerMethodField()
    output_template = serializers.SerializerMethodField()
    app_type_name = serializers.SerializerMethodField()
    discord_config = serializers.SerializerMethodField()
    slack_config = serializers.SerializerMethodField()
    web_config = serializers.SerializerMethodField()
    access_permission = serializers.SerializerMethodField()
    accessible_by = serializers.SerializerMethodField()
    read_accessible_by = serializers.SerializerMethodField()
    write_accessible_by = serializers.SerializerMethodField()
    last_modified_by_email = serializers.SerializerMethodField()
    template = serializers.SerializerMethodField()
    visibility = serializers.SerializerMethodField()
    has_live_version = serializers.SerializerMethodField()

    def get_logo(self, obj):
        profile = Profile.objects.get(user=obj.owner)
        return profile.logo if (profile.is_pro_subscriber() or profile.organization) else None

    def get_is_shareable(self, obj):
        profile = Profile.objects.get(user=obj.owner)
        return not profile.is_pro_subscriber() and not profile.organization

    def get_has_footer(self, obj):
        profile = Profile.objects.get(user=obj.owner)
        return not profile.is_pro_subscriber() and not profile.organization

    def get_last_modified_by_email(self, obj):
        return obj.last_modified_by.email if obj.last_modified_by and obj.has_write_permission(self._request_user) else None

    def get_owner_email(self, obj):
        return obj.owner.email if obj.has_write_permission(self._request_user) else None

    def get_output_template(self, obj):
        return convert_template_vars_from_legacy_format(obj.output_template) if obj.output_template else None

    def get_data(self, obj):
        app_data = AppData.objects.filter(
            app_uuid=obj.uuid).order_by('-created_at').first()
        if app_data and app_data.data:
            if not obj.has_write_permission(self._request_user):
                app_data.data.pop('processors', None)
            return app_data.data
        return None

    def get_has_live_version(self, obj):
        app_datas = AppData.objects.filter(
            app_uuid=obj.uuid, is_draft=False).first()
        return app_datas is not None

    def get_app_type_name(self, obj):
        return obj.type.name

    def get_processors(self, obj):
        data = self.get_data(obj)
        if data:
            return None

        processors = []
        if obj.has_write_permission(self._request_user) and obj.run_graph:
            nodes = obj.run_graph.all()

            entry_nodes = list(
                filter(
                    lambda x: x.entry_endpoint is None, nodes,
                ),
            )
            node = entry_nodes[0].exit_endpoint if entry_nodes else None
            while node:
                processors.append({
                    'input': node.input,
                    'config': node.config,
                    'api_backend': ApiBackendSerializer(instance=node.api_backend).data,
                    'endpoint': str(node.uuid),
                })
                node_to_find = node
                edge = list(
                    filter(
                        lambda x: x.entry_endpoint
                        == node_to_find, nodes,
                    ),
                )[0]

                node = edge.exit_endpoint if edge else None
        return processors

    def get_unique_processors(self, obj):
        if obj.has_write_permission(self._request_user):
            data = self.get_data(obj)
            processors = data.get('processors', []) if data else []
            unique_processors = []
            for processor in processors:
                if 'provider_slug' in processor and 'processor_slug' in processor:
                    name = f"{processor['provider_slug']} / {processor['processor_slug']}"
                    if name not in unique_processors:
                        unique_processors.append(name)
            return unique_processors

        return []

    def get_discord_config(self, obj):
        return obj.discord_config if obj.has_write_permission(self._request_user) else None

    def get_slack_config(self, obj):
        return obj.slack_config if obj.has_write_permission(self._request_user) else None

    def get_access_permission(self, obj):
        return AppAccessPermission.WRITE if obj.has_write_permission(self._request_user) else AppAccessPermission.READ

    def get_accessible_by(self, obj):
        return obj.accessible_by if obj.has_write_permission(self._request_user) else None

    def get_read_accessible_by(self, obj):
        return obj.read_accessible_by if obj.has_write_permission(self._request_user) else None

    def get_write_accessible_by(self, obj):
        return obj.write_accessible_by if obj.has_write_permission(self._request_user) else None

    def get_last_modified_by_email(self, obj):
        return obj.last_modified_by.email if (obj.last_modified_by and obj.has_write_permission(self._request_user)) else None

    def get_template(self, obj):
        if obj.template:
            return AppTemplateSerializer(instance=obj.template).data
        elif obj.template_slug is not None:
            app_template = get_app_template_by_slug(obj.template_slug)
            if app_template:
                return app_template.dict(exclude_none=True)
        return None

    def get_web_config(self, obj):
        return obj.web_config if obj.has_write_permission(self._request_user) else None

    def get_visibility(self, obj):
        return obj.visibility if obj.has_write_permission(self._request_user) else None

    class Meta:
        model = App
        fields = [
            'name', 'description', 'config', 'input_schema', 'data',
            'type', 'uuid', 'published_uuid', 'is_published', 'unique_processors',
            'input_ui_schema', 'output_template', 'created_at', 'last_updated_at',
            'logo', 'is_shareable', 'has_footer', 'domain', 'visibility', 'accessible_by',
            'access_permission', 'last_modified_by_email', 'owner_email', 'web_config',
            'slack_config', 'discord_config', 'app_type_name', 'processors', 'template',
            'read_accessible_by', 'write_accessible_by', 'has_live_version'
        ]


class AppTemplateCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AppTemplateCategory
        fields = ['name', 'slug']


class AppTemplateSerializer(serializers.ModelSerializer):
    class AppTemplateAppSerializer(serializers.ModelSerializer):
        processors = serializers.SerializerMethodField()
        input_fields = serializers.SerializerMethodField()

        def get_processors(self, obj):
            processors = []
            if obj.run_graph:
                nodes = obj.run_graph.all()

                entry_nodes = list(
                    filter(
                        lambda x: x.entry_endpoint is None, nodes,
                    ),
                )
                node = entry_nodes[0].exit_endpoint if entry_nodes else None
                while node:
                    processors.append({
                        'input': node.input,
                        'config': node.config,
                        'api_backend': ApiBackendSerializer(instance=node.api_backend).data,
                        'processor_slug': node.api_backend.slug,
                        'provider_slug': node.api_backend.api_provider.slug,
                        'endpoint': str(node.uuid),
                    })
                    node_to_find = node
                    edge = list(
                        filter(
                            lambda x: x.entry_endpoint
                            == node_to_find, nodes,
                        ),
                    )[0]

                    node = edge.exit_endpoint if edge else None
            return processors

        def get_input_fields(self, obj):
            app_data = AppData.objects.filter(
                app_uuid=obj.uuid).order_by('-created_at').first()
            if app_data:
                return app_data.data.get('input_fields', [])
            return []

        class Meta:
            model = App
            fields = [
                'config', 'input_schema', 'type',
                'input_ui_schema', 'output_template', 'processors',
                'input_fields'
            ]

    app = serializers.SerializerMethodField()
    pages = serializers.SerializerMethodField()
    categories = AppTemplateCategorySerializer(many=True)

    def get_app(self, obj):
        hide_details = self.context.get('hide_details', True)
        if hide_details:
            return None

        app_obj = App.objects.get(uuid=obj.app_uuid, is_cloneable=True)
        if app_obj is None:
            return None

        return AppTemplateSerializer.AppTemplateAppSerializer(instance=app_obj).data

    def get_pages(self, obj):
        hide_details = self.context.get('hide_details', True)
        if hide_details:
            return None

        app_template_handler_cls = AppTemplateFactory.get_app_template_handler(
            obj,
        )
        if app_template_handler_cls is None:
            return []
        return app_template_handler_cls.get_pages_schema()

    class Meta:
        model = AppTemplate
        fields = [
            'name', 'description', 'slug', 'app',
            'pages', 'categories', 'example_app_uuid',
        ]


class AppDataSerializer(serializers.ModelSerializer):

    data = serializers.SerializerMethodField()

    def get_data(self, obj):
        hide_details = self.context.get('hide_details', True)
        if hide_details:
            return None

        return obj.data

    class Meta:
        model = AppData
        fields = ['version', 'app_uuid', 'data',
                  'created_at', 'last_updated_at', 'is_draft', 'comment']


class AppHubSerializer(serializers.ModelSerializer):
    published_uuid = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    categories = AppTemplateCategorySerializer(many=True)

    def get_published_uuid(self, obj):
        return obj.app.published_uuid

    def get_name(self, obj):
        return obj.app.name

    def get_description(self, obj):
        return obj.app.description

    class Meta:
        model = AppHub
        fields = ['published_uuid', 'categories', 'name', 'description']


class CloneableAppSerializer(serializers.ModelSerializer):

    class CloneableAppRunGraphEntrySerializer(serializers.ModelSerializer):
        class CloneableAppEndpointSerializer(serializers.ModelSerializer):
            api_backend = ApiBackendSerializer()

            class Meta:
                model = Endpoint
                fields = [
                    'name', 'api_backend',
                    'description', 'is_app', 'config', 'input',
                ]
        entry_endpoint = CloneableAppEndpointSerializer()
        exit_endpoint = CloneableAppEndpointSerializer()

        class Meta:
            model = AppRunGraphEntry
            fields = ['id', 'entry_endpoint', 'exit_endpoint']

    type = AppTypeSerializer()
    run_graph = CloneableAppRunGraphEntrySerializer(many=True)

    class Meta:
        model = App
        fields = [
            'name', 'description', 'config', 'input_schema', 'data_transformer',
            'type', 'input_ui_schema', 'output_template', 'run_graph', 'published_uuid', 'is_published', 'domain', 'created_at', 'last_updated_at',
        ]


class AppSessionSerializer(serializers.ModelSerializer):
    app = AppSerializer()

    class Meta:
        model = AppSession
        fields = ['uuid', 'app']


class TestSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestSet
        fields = ['uuid', 'name', 'created_at', 'last_updated_at']


class TestCaseSerializer(serializers.ModelSerializer):
    testset_uuid = serializers.SerializerMethodField()

    def get_testset_uuid(self, obj):
        return str(obj.testset.uuid)

    class Meta:
        model = TestCase
        fields = [
            'uuid', 'input_data', 'expected_output',
            'testset_uuid', 'created_at', 'last_updated_at',
        ]
