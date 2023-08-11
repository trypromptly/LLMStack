import asyncio
import base64
import json
import logging
import os
import uuid
from collections import namedtuple

from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import logout
from django.db.models import Max
from django.http import Http404
from django.http import HttpResponseForbidden
from django.http import HttpResponseNotFound
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response as DRFResponse
from rest_framework.views import APIView

from .models import ApiBackend
from .models import ApiProvider
from .models import Endpoint
from base.models import Profile
from .models import Request
from .models import Response
from .models import RunEntry
from .providers.api_processors import ApiProcessorFactory
from .serializers import ApiBackendSerializer
from .serializers import ApiProviderSerializer
from .serializers import EndpointSerializer
from .serializers import HistorySerializer
from .serializers import LoginSerializer
from .serializers import ResponseSerializer
from apps.app_session_utils import create_app_session
from apps.app_session_utils import get_app_session_data
from play.actor import ActorConfig
from play.actors.bookkeeping import BookKeepingActor
from play.actors.input import InputActor
from play.actors.input import InputRequest
from play.actors.output import OutputActor
from play.coordinator import Coordinator

Schema = namedtuple('Schema', 'type default is_required')

# Generate URL safe random code for sharing


def share_code_genrate(code_length=6):
    return base64.urlsafe_b64encode(os.urandom(code_length)).decode('utf-8')[:code_length]


def get_api_schema(api_backend):
    api_request_schema = {}
    required = []
    if api_backend.params and 'required' in api_backend.params:
        required = api_backend.params['required']

    if not api_backend.params or 'properties' not in api_backend.params:
        return api_request_schema

    for key, value in api_backend.params['properties'].items():
        if 'default' not in value:
            continue
        value_type = value['type']
        value_default = value['default']
        if value_default == 'null':
            value_default = None
        value_is_required = True if key in required else False
        schema = Schema(value_type, value_default, value_is_required)
        api_request_schema[key] = schema

    return api_request_schema


def get_final_api_params(api_schema, endpoint_params, versioned_endpoint_params, request_params):

    request_body = {}
    # Start with API defaults
    for key, value in api_schema.items():
        request_body[key] = value.default

    if endpoint_params:
        # Override with params in Endpoint
        for key, value in endpoint_params.items():
            request_body[key] = value

    if versioned_endpoint_params:
        # Override with params in Versioned Endpoint
        for key, value in versioned_endpoint_params.items():
            request_body[key] = value

    # Override with params provided in request
    if request_params:
        # Override with API request params
        for key, value in request_params.items():
            request_body[key] = value

    return request_body


class ResponseViewSet(viewsets.ViewSet):
    def list(self, request):
        requests_queryset = Request.objects.all().filter(
            endpoint__in=Endpoint.objects.all().filter(owner=request.user),
        )
        queryset = Response.objects.all().filter(
            request__in=requests_queryset,
        ).order_by('-created_on')[:20]
        serializer = ResponseSerializer(queryset, many=True)
        return DRFResponse(serializer.data)


logger = logging.getLogger(__name__)


def sanitize_json(json_obj):
    """
    Sanitizes a JSON object to escape double quotes in values.
    """
    if isinstance(json_obj, dict):
        # If the object is a dictionary, traverse its values recursively
        for key, value in json_obj.items():
            json_obj[key] = sanitize_json(value)
    elif isinstance(json_obj, list):
        # If the object is a list, traverse its values recursively
        for i, value in enumerate(json_obj):
            json_obj[i] = sanitize_json(value)
    elif isinstance(json_obj, str):
        # If the object is a string, replace double quotes with escaped double quotes
        json_obj = json_obj.replace('"', '\\"')
    return json_obj


class EndpointViewSet(viewsets.ViewSet):
    def list(self, request):
        queryset = Endpoint.objects.all().filter(owner=request.user)
        serializer = EndpointSerializer(queryset, many=True)
        return DRFResponse(serializer.data)

    def create(self, request):
        name = request.data.get('name')
        api_backend = get_object_or_404(
            ApiBackend, id=request.data.get('api_backend'),
        )
        owner = request.user
        param_values = request.data.get('param_values', {})
        is_live = request.data.get('is_live', False)
        if isinstance(param_values, str):
            param_values = json.loads(param_values)
        post_processor = request.data.get('post_processor', '')
        draft = request.data.get('draft', False)
        prompt = request.data.get('prompt', '')
        config = request.data.get('config', {})
        input = request.data.get('input', {})
        parent_uuid = None if 'parent_uuid' not in request.data else request.data.get(
            'parent_uuid',
        )
        description = request.data.get(
            'description',
        ) if 'description' in request.data else 'Initial version'

        endpoint_object = Endpoint(
            name=name, api_backend=api_backend, owner=owner, param_values=param_values, post_processor=post_processor,
            draft=draft, prompt=prompt, parent_uuid=parent_uuid, description=description, is_live=is_live, config=config, input=input,
        )
        endpoint_object.save()

        return DRFResponse(EndpointSerializer(instance=endpoint_object).data)

    def delete(self, request, id, force_delete_app=False):
        endpoint_object = get_object_or_404(Endpoint, uuid=uuid.UUID(id))

        if endpoint_object.owner != request.user:
            return PermissionDenied()

        if endpoint_object.is_app and not force_delete_app:
            return DRFResponse({'error': 'Cannot delete an app endpoint.'}, status=400)

        if str(endpoint_object.parent_uuid) == id and endpoint_object.version == 0:
            # We are asked to delete the parent endpoint. Delete all versions
            versioned_endpoints = Endpoint.objects.filter(
                parent_uuid=endpoint_object.parent_uuid)
            versioned_endpoints.delete()
        else:
            endpoint_object.delete()

        return DRFResponse(status=204)

    @ action(detail=True, methods=['patch'])
    def patch(self, request):
        should_update = False
        endpoint = get_object_or_404(
            Endpoint, parent_uuid=request.data.get(
                'parent_uuid',
            ), version=request.data.get('version'),
        )
        update_keys = []
        if 'name' in request.data:
            endpoint.name = request.data.get('name')
            update_keys.append('name')
            should_update = True

        if 'is_live' in request.data:
            endpoint.is_live = request.data.get('is_live')
            update_keys.append('is_live')
            should_update = True

        if 'draft' in request.data:
            endpoint.draft = request.data.get('draft')
            update_keys.append('draft')
            should_update = True

        if 'description' in request.data:
            endpoint.description = request.data.get('description')
            update_keys.append('description')
            should_update = True

        if should_update:
            endpoint.save(update_fields=update_keys)

        queryset = Endpoint.objects.get(
            parent_uuid=request.data.get(
                'parent_uuid',
            ), version=request.data.get('version'),
        )
        serializer = EndpointSerializer(queryset)
        return DRFResponse(serializer.data)

    def get(self, request, id):
        endpoint_object = get_object_or_404(Endpoint, uuid=id)
        if endpoint_object.owner != request.user:
            return PermissionDenied()
        return DRFResponse(EndpointSerializer(instance=endpoint_object).data)

    # Update will create a new version of endpoint and save into the db
    def update(self, request, id):
        owner = request.user
        endpoint_object = get_object_or_404(Endpoint, uuid=id)

        if endpoint_object.owner != request.user:
            return PermissionDenied()
        param_values = request.data.get(
            'param_values', endpoint_object.param_values,
        )
        if isinstance(param_values, str):
            param_values = json.loads(param_values)
        post_processor = request.data.get(
            'post_processor', endpoint_object.post_processor,
        )
        draft = request.data.get('draft', False)
        prompt = request.data.get('prompt', endpoint_object.prompt)
        if endpoint_object.parent_uuid:
            # version > 1
            parent_uuid = endpoint_object.parent_uuid
        else:
            # If this is version 1 update
            parent_uuid = id

        latest_endpoint_object = Endpoint.objects.filter(
            uuid=uuid.UUID(parent_uuid),
        ).order_by('-version').first()
        version = getattr(latest_endpoint_object, 'version') + 1
        description = request.data.get(
            'description', 'Version {}'.format(version),
        )
        new_endpoint_object = Endpoint(
            name=endpoint_object.name, api_backend=endpoint_object.api_backend, owner=owner, param_values=param_values, post_processor=post_processor,
            draft=draft, prompt=prompt, version=version, parent_uuid=parent_uuid, description=description,
        )
        new_endpoint_object.save()
        return DRFResponse(EndpointSerializer(instance=new_endpoint_object).data)

    @ action(detail=True, methods=['post'])
    @ csrf_exempt
    def invoke_api(self, request, id, version=None):
        # If version is not provided, find latest live endpoint
        endpoint = None
        if version is None:
            endpoint = Endpoint.objects.filter(
                parent_uuid=uuid.UUID(
                    id,
                ), is_live=True,
            ).order_by('-version').first()
        else:
            endpoint = Endpoint.objects.filter(
                parent_uuid=uuid.UUID(id), version=version,
            ).first()

        # Couldn't find a live version. Find latest version for endpoint
        if not endpoint:
            endpoint = Endpoint.objects.filter(
                parent_uuid=uuid.UUID(id),
            ).order_by('-version').first()

        if not endpoint:
            return HttpResponseNotFound('Invalid endpoint')

        if request.user != endpoint.owner:
            return HttpResponseForbidden('Invalid ownership')

        bypass_cache = request.data.get('bypass_cache', False)

        # Create request object for this versioned endpoint
        template_values = request.data['template_values'] if 'template_values' in request.data else {
        }
        config = request.data['config'] if 'config' in request.data else {}
        input = request.data['input'] if 'input' in request.data else {}

        stream = request.data.get('stream', False)

        request_user_agent = request.META.get(
            'HTTP_USER_AGENT', 'Streaming API Client' if stream else 'API Client',
        )
        request_location = request.headers.get('X-Client-Geo-Location', '')
        request_ip = request_ip = request.headers.get(
            'X-Forwarded-For', request.META.get(
                'REMOTE_ADDR', '',
            ),
        ).split(',')[0].strip() or request.META.get('HTTP_X_REAL_IP', '')

        request_user_email = ''
        if request.user and request.user.email and len(request.user.email) > 0:
            request_user_email = request.user.email
        elif request.user and request.user.username and len(request.user.username) > 0:
            # Use username as email if email is not set
            request_user_email = request.user.username
            
        input_request = InputRequest(
            request_endpoint_uuid=str(endpoint.uuid), request_app_uuid='',
            request_app_session_key='', request_owner=request.user,
            request_uuid=str(uuid.uuid4()), request_user_email=request_user_email,
            request_ip=request_ip, request_location=request_location,
            request_user_agent=request_user_agent, request_body=request.data,
            request_content_type=request.content_type,
        )
        logger.info("Request: {}".format(input_request))

        try:
            invoke_result = self.run_endpoint(
                endpoint=endpoint, run_as_user=request.user, input_request=input_request, template_values=template_values, bypass_cache=bypass_cache, input=input, config=config, app_session=None, stream=stream,
            )

            if stream:
                response = StreamingHttpResponse(
                    streaming_content=invoke_result, content_type='application/json',
                )
                response.is_async = True
                return response
        except Exception as e:
            invoke_result = {'id': -1, 'errors': [str(e)]}

        if 'errors' in invoke_result:
            return DRFResponse({'errors': invoke_result['errors']}, status=500)

        return DRFResponse(invoke_result)

    def run_endpoint(self, endpoint, run_as_user, input_request, template_values={}, bypass_cache=False, input={}, config={}, app_session=None, output_stream=None, stream=False):
        profile = get_object_or_404(Profile, user=run_as_user)

        # Merge config and input with endpoint config, input
        config = {**endpoint.config, **config}
        input = {**endpoint.input, **input}

        vendor_env = profile.get_vendor_env()

        # Pick a processor
        processor_cls = ApiProcessorFactory.get_api_processor(
            endpoint.api_backend.slug,
        )

        if not app_session:
            app_session = create_app_session(None, str(uuid.uuid4()))

        app_session_data = get_app_session_data(
            app_session, endpoint,
        )

        actor_configs = [
            ActorConfig(
                name=str(endpoint.uuid), template_key='processor', actor=processor_cls, dependencies=['input'], kwargs={
                    'config': config, 'input': input, 'env': vendor_env, 'session_data': app_session_data['data'] if app_session_data and 'data' in app_session_data else {},
                },
                output_cls=processor_cls.get_output_cls(),
            ),
            ActorConfig(
                name='input', template_key='', actor=InputActor, kwargs={
                    'input_request': input_request,
                },
            ),
            ActorConfig(
                name='output', template_key='output',
                actor=OutputActor, dependencies=['processor'], kwargs={'template': '{{ processor | tojson }}'},
            ),
            ActorConfig(
                name='bookkeeping', template_key='bookkeeping', actor=BookKeepingActor, dependencies=['input', 'output'], kwargs={
                    'processor_configs': {
                        str(endpoint.uuid): {
                            'processor': endpoint,
                            'app_session': None,
                            'app_session_data': None,
                            'template_key': 'processor',
                        },
                    },
                },
            ),
        ]

        try:
            coordinator_ref = Coordinator.start(
                session_id=app_session['uuid'], actor_configs=actor_configs,
            )
            coordinator = coordinator_ref.proxy()

            output = None
            input_actor = coordinator.get_actor('input').get().proxy()
            output_actor = coordinator.get_actor('output').get().proxy()
            output_iter = None
            if input_actor and output_actor:
                input_actor.write(template_values).get()
                output_iter = output_actor.get_output().get(
                ) if not stream else output_actor.get_output_stream().get()

            if stream:
                # Return a wrapper over output_iter where we call next() on output_iter and yield the result
                async def stream_output():
                    try:
                        while True:
                            await asyncio.sleep(0.0001)
                            output = next(output_iter)
                            yield json.dumps({'output': output['processor']}) + '\n'
                    except StopIteration:
                        coordinator_ref.stop()
                    except Exception as e:
                        logger.exception(e)
                        coordinator_ref.stop()
                        raise e
                return stream_output()

            for output in output_iter:
                # Iterate through output_iter to get the final output
                pass

            coordinator_ref.stop()

        except Exception as e:
            logger.exception(e)
            raise Exception(f'Error starting coordinator: {e}')

        return {'output': json.loads(output)} if 'errors' not in output else output


class ApiProviderViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @ method_decorator(cache_page(60*60*24))
    def list(self, request):
        queryset = ApiProvider.objects.all()
        serializer = ApiProviderSerializer(queryset, many=True)
        return DRFResponse(serializer.data)


class ApiBackendViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def list(self, request):
        queryset = ApiBackend.objects.all()
        serializer = ApiBackendSerializer(queryset, many=True)
        return DRFResponse(serializer.data)

    @ method_decorator(cache_page(60*60*24))
    def filtered(self, request):
        api_provider_id = request.GET.get('apiprovider')
        queryset = ApiBackend.objects.all().filter(api_provider=api_provider_id)
        serializer = ApiBackendSerializer(queryset, many=True)
        return DRFResponse(serializer.data)


class HistoryViewSet(viewsets.ModelViewSet):
    paginate_by = 20
    permission_classes = [IsAuthenticated]

    def list(self, request):
        app_uuid = request.GET.get('app_uuid', None)
        session_key = request.GET.get('session_key', None)
        request_user_email = request.GET.get('request_user_email', None)
        endpoint_uuid = request.GET.get('endpoint_uuid', None)
        detail = request.GET.get('detail', False)

        filters = {
            'owner': request.user,
        }
        if app_uuid and app_uuid != 'null':
            filters['app_uuid'] = app_uuid
        if session_key and session_key != 'null':
            filters['session_key'] = session_key
        if request_user_email and request_user_email != 'null':
            filters['request_user_email'] = request_user_email
        if endpoint_uuid and endpoint_uuid != 'null':
            filters['endpoint_uuid'] = endpoint_uuid

        queryset = RunEntry.objects.all().filter(**filters).order_by('-created_at')
        page = self.paginate_queryset(queryset)
        if page is not None:
            response = self.get_paginated_response(
                HistorySerializer(page, many=True, context={
                                  'hide_details': not detail}).data,
            )
        else:
            response = HistorySerializer(
                queryset, many=True, context={'hide_details': not detail},
            )

        return DRFResponse(response.data)

    def list_sessions(self, request):
        app_uuid = request.GET.get('app_uuid', None)
        filters = {
            'owner': request.user,
            'session_key__isnull': False,
        }

        if app_uuid and app_uuid != 'null':
            filters['app_uuid'] = app_uuid

        queryset = RunEntry.objects.all().filter(
            **filters,
        ).values(
            'session_key', 'app_uuid', 'request_user_email', 'platform_data',
        ).annotate(
            latest_created_at=Max('created_at'),
        ).order_by('-latest_created_at').distinct()

        page = self.paginate_queryset(queryset)
        if page is not None:
            response = self.get_paginated_response(page)
        else:
            response = queryset
        return DRFResponse(response.data)

    def get(self, request, request_uuid):
        object = RunEntry.objects.all().filter(
            request_uuid=request_uuid, owner=request.user,
        ).first()
        if not object:
            raise Http404('Invalid request uuid')

        return DRFResponse(HistorySerializer(instance=object).data)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.data.get('username')
            password = serializer.data.get('password')
            user = authenticate(username=username, password=password)
            if user:
                login(request=request, user=user)
                return DRFResponse({'message': 'Login successful'})

        return DRFResponse('Error in signing in', status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    def post(self, request):
        logout(request)
        return DRFResponse({'message': 'Logout successful'})
