import logging
import uuid

from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.permissions import BasePermission
from rest_framework.response import Response as DRFResponse

from llmstack.apps.models import App, AppVisibility
from llmstack.apps.serializers import AppSerializer
from llmstack.datasources.models import DataSource, DataSourceEntry, DataSourceVisibility
from llmstack.datasources.serializers import DataSourceEntrySerializer, DataSourceSerializer
from llmstack.datasources.types import DataSourceTypeFactory
from organizations.models import Organization
from organizations.models import OrganizationSettings
from organizations.serializers import OrganizationSerializer
from organizations.serializers import OrganizationSettingsSerializer
from llmstack.base.models import Profile

logger = logging.getLogger(__name__)


class OrgPermission(BasePermission):
    def has_permission(self, request, view):
        profile = get_object_or_404(Profile, user=request.user)
        organization = profile.organization
        if organization:
            return True

        return False


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer

    def get(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        organization = profile.organization
        if organization is None:
            return DRFResponse(None)

        return DRFResponse(OrganizationSerializer(instance=organization).data)


class OrganizationSettingsViewSet(viewsets.ModelViewSet):
    queryset = OrganizationSettings.objects.all()
    serializer_class = OrganizationSettingsSerializer

    def get(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        organization = profile.organization
        if organization is None:
            raise Exception('User is not part of an organization')

        if not organization.is_admin(request.user):
            raise Exception('User is not an admin of the organization')

        organization_settings = OrganizationSettings.objects.get(
            organization=organization,
        )

        if organization_settings is None:
            raise Exception('Organization settings not found')

        return DRFResponse(OrganizationSettingsSerializer(instance=organization_settings).data)

    def patch(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        organization = profile.organization
        if organization is None:
            raise Exception('User is not part of an organization')

        if not organization.is_admin(request.user):
            raise Exception('User is not an admin of the organization')

        organization_settings = OrganizationSettings.objects.get(
            organization=organization,
        )
        if organization_settings is None:
            raise Exception('Organization settings not found')

        # Get logo as data url and save it to ImageField
        logo_data_url = request.data.get('logo', None)
        if logo_data_url and logo_data_url != organization_settings.logo.url:
            import base64
            from django.core.files.base import ContentFile
            format, imgstr = logo_data_url.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr),
                name=organization.slug + '_logo.' + ext,
            )
            organization_settings.logo = data

        organization_settings.default_app_visibility = request.data.get(
            'default_app_visibility', AppVisibility.PUBLIC,
        )
        organization_settings.max_app_visibility = request.data.get(
            'max_app_visibility', AppVisibility.PUBLIC,
        )
        organization_settings.allow_user_keys = request.data.get(
            'allow_user_keys', True,
        )

        organization_settings.azure_openai_api_key = organization_settings.encrypt_value(
            request.data.get(
                'azure_openai_api_key', None,
            ),
        )
        organization_settings.openai_key = organization_settings.encrypt_value(
            request.data.get(
                'openai_key', None,
            ),
        )
        organization_settings.stabilityai_key = organization_settings.encrypt_value(
            request.data.get(
                'stabilityai_key', None,
            ),
        )
        organization_settings.cohere_key = organization_settings.encrypt_value(
            request.data.get(
                'cohere_key', None,
            ),
        )
        organization_settings.forefrontai_key = organization_settings.encrypt_value(
            request.data.get(
                'forefrontai_key', None,
            ),
        )
        organization_settings.elevenlabs_key = organization_settings.encrypt_value(
            request.data.get(
                'elevenlabs_key', None,
            ),
        )
        organization_settings.aws_secret_access_key = organization_settings.encrypt_value(
            request.data.get(
                'aws_secret_access_key', None,
            ),
        )
        organization_settings.vectorstore_weaviate_api_key = organization_settings.encrypt_value(
            request.data.get(
                'vectorstore_weaviate_api_key', None,
            ),
        )

        organization_settings.azure_openai_endpoint = request.data.get(
            'azure_openai_endpoint', None,
        )
        organization_settings.aws_access_key_id = request.data.get(
            'aws_access_key_id', None,
        )
        organization_settings.aws_default_region = request.data.get(
            'aws_default_region', None,
        )
        organization_settings.localai_api_key = organization_settings.encrypt_value(
            request.data.get(
                'localai_api_key', None,
            ),
        )
        organization_settings.localai_base_url = request.data.get(
            'localai_base_url', None,
        )
        organization_settings.anthropic_api_key = organization_settings.encrypt_value(
            request.data.get(
                'anthropic_api_key', None,
            ),
        )
        organization_settings.vectorstore_weaviate_url = request.data.get(
            'vectorstore_weaviate_url', None,
        )
        organization_settings.vectorstore_weaviate_text2vec_openai_module_config = request.data.get(
            'vectorstore_weaviate_text2vec_openai_module_config', None,
        )
        organization_settings.use_own_vectorstore = request.data.get(
            'use_own_vectorstore', False,
        )
        organization_settings.use_azure_openai_embeddings = request.data.get(
            'use_azure_openai_embeddings', False,
        )
        organization_settings.embeddings_api_rate_limit = request.data.get(
            'embeddings_api_rate_limit', 300,
        )

        organization_settings.save()

        return DRFResponse(OrganizationSettingsSerializer(instance=organization_settings).data)


class OrganizationMembersViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [OrgPermission]

    def get(self, request):
        organization = get_object_or_404(
            Profile, user=self.request.user,
        ).organization

        if organization is None:
            raise Exception('User is not part of an organization')

        if not organization.is_admin(request.user):
            raise Exception('User is not an admin of the organization')

        # Convert this to a serializer
        users = [{'first_name': profile.user.first_name, 'last_name': profile.user.last_name, 'email': profile.user.email} for profile in Profile.objects.filter(
            organization=organization,
        )]

        return DRFResponse(users)


class OrganizationAppsViewSet(viewsets.ModelViewSet):
    queryset = App.objects.all()
    serializer_class = AppSerializer
    permission_classes = [OrgPermission]

    def get(self, request):
        organization = get_object_or_404(
            Profile, user=self.request.user,
        ).organization

        if organization is None:
            raise Exception('User is not part of an organization')

        # Convert this to a serializer
        apps = [{'name': app.name, 'published_uuid': app.published_uuid, 'type': app.type.name, 'owner_email': app.owner.email} for app in App.objects.filter(
            owner__in=Profile.objects.filter(organization=organization).values('user'), visibility__gte=AppVisibility.ORGANIZATION, is_published=True,
        )]

        return DRFResponse(apps)


class OrganizationDataSourceViewSet(viewsets.ModelViewSet):
    queryset = DataSource.objects.all()
    permission_classes = [OrgPermission]
    serializer_class = DataSourceSerializer

    """
    API endpoint that allows organization data sources to be viewed or edited.
    """

    def _get_all_users_in_organization(self):
        organization = get_object_or_404(
            Profile, user=self.request.user,
        ).organization

        if organization is None:
            raise Exception('User is not part of an organization')

        return Profile.objects.filter(
            organization=organization,
        ).values('user')

    def get_queryset(self):
        return super().get_queryset().filter(owner__in=self._get_all_users_in_organization(), visibility=DataSourceVisibility.ORGANIZATION)

    def _get_object_or_404(self, uid):
        datasource_object = self.get_queryset().filter(uuid=uuid.UUID(uid)).first()
        logger.info('datasource_object: %s', datasource_object)
        if datasource_object is None:
            raise Exception('Data source not found')
        return datasource_object

    def get(self, request, uid=None):
        if uid:
            datasource_object = self._get_object_or_404(uid)
            return DRFResponse(DataSourceSerializer(instance=datasource_object).data)

        return DRFResponse(
            DataSourceSerializer(
                instance=self.get_queryset(), many=True,
            ).data,
        )

    def getEntries(self, request, uid):
        datasource_object = self._get_object_or_404(uid)
        datasource_entries = DataSourceEntry.objects.filter(
            datasource=datasource_object,
        )
        return DRFResponse(DataSourceEntrySerializer(instance=datasource_entries, many=True).data)

    def add_entry(self, request, uid=None):
        datasource_object = get_object_or_404(DataSource, uuid=uuid.UUID(uid))
        if datasource_object.owner != request.user:
            return DRFResponse('Action not allowed', status=403)

        datasource_object.visibility = DataSourceVisibility.ORGANIZATION
        datasource_object.save()

        return DRFResponse(DataSourceSerializer(instance=datasource_object).data)

    def delete(self, request, uid=None):
        datasource_object = datasource_object = self._get_object_or_404(uid)
        if datasource_object.owner != request.user:
            return DRFResponse('Action not allowed', status=403)

        datasource_object.visibility = DataSourceVisibility.PRIVATE
        datasource_object.save()
        return DRFResponse(DataSourceSerializer(instance=datasource_object).data)


class OrganizationDataSourceEntryViewSet(viewsets.ModelViewSet):
    queryset = DataSourceEntry.objects.all()
    serializer_class = DataSourceEntrySerializer
    permission_classes = [OrgPermission]

    def _get_all_users_in_organization(self):
        organization = get_object_or_404(
            Profile, user=self.request.user,
        ).organization

        if organization is None:
            raise Exception('User is not part of an organization')

        return Profile.objects.filter(
            organization=organization,
        ).values('user')

    def _get_datasource_entry_object_or_404(self, request, uid):
        request_user_profile = get_object_or_404(Profile, user=request.user)
        datasource_entry_object = get_object_or_404(
            DataSourceEntry, uuid=uuid.UUID(uid),
        )
        datasource_entry_object_owner_profile = get_object_or_404(
            Profile, user=datasource_entry_object.datasource.owner,
        )
        if request_user_profile.organization != datasource_entry_object_owner_profile.organization:
            raise Http404('Data source entry not found')

        if datasource_entry_object.datasource.visibility != DataSourceVisibility.ORGANIZATION:
            raise Http404('Data source entry not found')

        return datasource_entry_object

    def get(self, request, uid=None):
        if uid:
            datasource_entry_object = self._get_datasource_entry_object_or_404(
                request, uid,
            )
            return DRFResponse(DataSourceEntrySerializer(instance=datasource_entry_object).data)

        datasources = DataSource.objects.filter(
            owner__in=self._get_all_users_in_organization(
            ), visibility=DataSourceVisibility.ORGANIZATION,
        )

        datasource_entries = DataSourceEntry.objects.filter(
            datasource__in=datasources,
        )
        return DRFResponse(DataSourceEntrySerializer(instance=datasource_entries, many=True).data)

    def text_content(self, request, uid):
        datasource_entry_object = self._get_datasource_entry_object_or_404(
            request, uid,
        )

        datasource_type = datasource_entry_object.datasource.type
        datasource_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
            datasource_type,
        )
        datasource_handler = datasource_handler_cls(
            datasource_entry_object.datasource,
        )
        content = datasource_handler.get_entry_text(
            datasource_entry_object.config,
        )
        return DRFResponse({'content': content})
