import base64
import json
import logging

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from flags.sources import get_flags
from flags.state import flag_enabled
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response as DRFResponse

from .models import Profile
from .serializers import ProfileSerializer
from llmstack.apps.models import App
from django.conf import settings

logger = logging.getLogger(__name__)


class ProfileViewSet(viewsets.ViewSet):

    def get(self, request):
        queryset = Profile.objects.get(user=request.user)
        serializer = ProfileSerializer(queryset)
        return DRFResponse(serializer.data)

    @action(detail=True, methods=['get'])
    def me(self, request):
        return HttpResponse(json.dumps(
            {'user': request.user.email}), content_type='application/json')

    @action(detail=True, methods=['get'])
    def get_flags(self, request):
        try:
            flags = get_flags(sources=settings.FLAG_SOURCES)
            flag_values = {}
            for flag_name, flag in flags.items():
                flag_values[flag_name] = flag.check_state(request=request)
            return DRFResponse(flag_values)
        except Exception as e:
            logger.exception(e)
            return DRFResponse({'error': str(e)},
                               status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'])
    def patch(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        should_update = False
        if 'openai_key' in request.data and flag_enabled(
                'CAN_ADD_KEYS', request=request):
            should_update = True
            openai_key = request.data.get('openai_key')
            if openai_key and len(openai_key) > 0:
                profile.openai_key = profile.encrypt_value(
                    openai_key,
                ).decode('utf-8')
            else:
                profile.openai_key = ''
        if 'stabilityai_key' in request.data and flag_enabled(
                'CAN_ADD_KEYS', request=request):
            should_update = True
            stabilityai_key = request.data.get('stabilityai_key')
            if stabilityai_key and len(stabilityai_key) > 0:
                profile.stabilityai_key = profile.encrypt_value(
                    stabilityai_key,
                ).decode('utf-8')
            else:
                profile.stabilityai_key = ''
        if 'cohere_key' in request.data and flag_enabled(
                'CAN_ADD_KEYS', request=request):
            should_update = True
            cohere_key = request.data.get('cohere_key')
            if cohere_key and len(cohere_key) > 0:
                profile.cohere_key = profile.encrypt_value(
                    cohere_key,
                ).decode('utf-8')
            else:
                profile.cohere_key = ''

        if 'forefrontai_key' in request.data and flag_enabled(
                'CAN_ADD_KEYS', request=request):
            should_update = True
            forefrontai_key = request.data.get('forefrontai_key')
            if forefrontai_key and len(forefrontai_key) > 0:
                profile.forefrontai_key = profile.encrypt_value(
                    forefrontai_key,
                ).decode('utf-8')
            else:
                profile.forefrontai_key = ''

        if 'elevenlabs_key' in request.data and flag_enabled(
                'CAN_ADD_KEYS', request=request):
            should_update = True
            elevenlabs_key = request.data.get('elevenlabs_key')
            if elevenlabs_key and len(elevenlabs_key) > 0:
                profile.elevenlabs_key = profile.encrypt_value(
                    elevenlabs_key,
                ).decode('utf-8')
            else:
                profile.elevenlabs_key = ''

        if 'google_service_account_json_key' in request.data and flag_enabled(
                'CAN_ADD_KEYS', request=request):
            should_update = True
            try:
                google_service_account_json_key = json.loads(
                    base64.b64decode(
                        request.data.get(
                            'google_service_account_json_key', '{}',
                        ),
                    ).decode().strip(),
                )

                if google_service_account_json_key and len(
                        google_service_account_json_key.keys()) > 0:
                    profile.google_service_account_json_key = profile.encrypt_value(
                        json.dumps(
                            google_service_account_json_key,
                        ),
                    ).decode('utf-8')
                else:
                    profile.google_service_account_json_key = ''
            except Exception as e:
                # This is an API key
                encrypted_value = profile.encrypt_value(
                    request.data['google_service_account_json_key'],
                )
                if encrypted_value:
                    profile.google_service_account_json_key = encrypted_value.decode(
                        'utf-8')
                else:
                    profile.google_service_account_json_key = ''

        if 'azure_openai_api_key' in request.data and flag_enabled(
                'CAN_ADD_KEYS', request=request):
            should_update = True
            azure_openai_api_key = request.data.get('azure_openai_api_key')
            if azure_openai_api_key and len(azure_openai_api_key) > 0:
                profile.azure_openai_api_key = profile.encrypt_value(
                    azure_openai_api_key,
                ).decode('utf-8')
            else:
                profile.azure_openai_api_key = ''
        if 'localai_api_key' in request.data and flag_enabled(
                'CAN_ADD_KEYS', request=request):
            should_update = True
            localai_api_key = request.data.get('localai_api_key')
            if localai_api_key and len(localai_api_key) > 0:
                profile.localai_api_key = profile.encrypt_value(
                    localai_api_key,
                ).decode('utf-8')
            else:
                profile.localai_api_key = ''

        if 'localai_base_url' in request.data and flag_enabled(
                'CAN_ADD_KEYS', request=request):
            should_update = True
            localai_base_url = request.data.get('localai_base_url')
            if localai_base_url and len(localai_base_url) > 0:
                profile.localai_base_url = localai_base_url
            else:
                profile.localai_base_url = ''

        if 'anthropic_api_key' in request.data and flag_enabled(
                'CAN_ADD_KEYS', request=request):
            should_update = True
            anthropic_api_key = request.data.get('anthropic_api_key')
            if anthropic_api_key and len(anthropic_api_key) > 0:
                profile.anthropic_api_key = profile.encrypt_value(
                    anthropic_api_key,
                ).decode('utf-8')
            else:
                profile.anthropic_api_key = ''

        if 'logo' in request.data:
            should_update = True
            logo = request.data.get('logo')
            profile.logo = logo

        if 'domains' in request.data and flag_enabled(
                'CAN_ADD_APP_DOMAIN', request=request):
            user_published_apps = App.objects.filter(
                owner=request.user, is_published=True,
            )
            for app in user_published_apps:
                user_provided_domain_name = None

                for domain in request.data.get('domains'):
                    if str(app.uuid) == domain['uuid']:
                        user_provided_domain_name = domain['domain']

                app.domain = user_provided_domain_name
                app.save(update_fields=['domain'])

        if should_update:
            profile.save(update_fields=request.data.keys())

        queryset = Profile.objects.get(user=request.user)
        serializer = ProfileSerializer(queryset)
        return DRFResponse(serializer.data)
