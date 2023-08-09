import logging
import uuid

from channels.db import database_sync_to_async
from django.core.validators import validate_email
from django.db.models import Q
from django.forms import ValidationError
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.clickjacking import xframe_options_exempt
from flags.state import flag_enabled
from pydantic import BaseModel
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response as DRFResponse

from processors.apis import EndpointViewSet

from .models import App
from .models import AppAccessPermission
from .models import AppHub
from .models import AppRunGraphEntry
from .models import AppTemplate
from .models import AppType
from .models import AppVisibility
from .models import TestCase
from .models import TestSet
from .serializers import AppHubSerializer
from .serializers import AppSerializer
from .serializers import AppTemplateSerializer
from .serializers import AppTypeSerializer
from .serializers import CloneableAppSerializer
from .serializers import TestCaseSerializer
from .serializers import TestSetSerializer
from apps.handlers.app_runner_factory import AppRunerFactory
from apps.integration_configs import DiscordIntegrationConfig
from apps.integration_configs import SlackIntegrationConfig
from apps.integration_configs import WebIntegrationConfig
from emails.sender import EmailSender
from emails.templates.factory import EmailTemplateFactory
from processors.models import ApiBackend
from processors.models import Endpoint
from base.models import Profile

logger = logging.getLogger(__name__)


class AppOutputModel(BaseModel):
    output: dict


class AppRunnerException(Exception):
    status_code = 400
    details = None
    json_details = None


class AppTypeViewSet(viewsets.ViewSet):
    @method_decorator(cache_page(60*60*24))
    def get(self, request):
        queryset = AppType.objects.all()
        serializer = AppTypeSerializer(queryset, many=True)
        return DRFResponse(serializer.data)


class AppViewSet(viewsets.ViewSet):
    def get_permissions(self):
        if self.action == 'getByPublishedUUID' or self.action == 'run' or self.action == 'run_slack' or self.action == 'run_discord':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_processors_from_run_graph(self, run_graph):
        processors = []
        if not run_graph:
            return processors

        entry_node = list(
            filter(
                lambda x: x['entry_endpoint'] is None, run_graph,
            ),
        )[0]
        node = entry_node['exit_endpoint']
        while node:
            processors.append({
                'input': node['input'],
                'config': {},
                'api_backend': node['api_backend'],
            })
            node_to_find = node
            edge = list(
                filter(
                    lambda x: x['entry_endpoint']
                    == node_to_find, run_graph,
                ),
            )[0]

            node = edge['exit_endpoint'] if edge else None
        return processors

    def get(self, request, uid=None):
        fields = request.query_params.get('fields', None)
        if fields:
            fields = fields.split(',')

        if uid:
            app = get_object_or_404(
                App,
                Q(uuid=uuid.UUID(uid), owner=request.user) |
                Q(uuid=uuid.UUID(uid), accessible_by__contains=[
                  request.user.email], visibility=AppVisibility.PRIVATE, is_published=True),
            )
            serializer = AppSerializer(
                instance=app, fields=fields, request_user=request.user,
            )
            return DRFResponse(serializer.data)

        queryset = App.objects.all().filter(owner=request.user).order_by('-created_at')
        serializer = AppSerializer(
            queryset, many=True, fields=fields, request_user=request.user,
        )
        return DRFResponse(serializer.data)

    def getShared(self, request):
        fields = request.query_params.get('fields', None)
        if fields:
            fields = fields.split(',')

        queryset = App.objects.all().filter(
            accessible_by__contains=[
                request.user.email,
            ], visibility=AppVisibility.PRIVATE, is_published=True,
        ).order_by('-last_updated_at')
        serializer = AppSerializer(
            queryset, many=True, fields=fields, request_user=request.user,
        )
        return DRFResponse(serializer.data)

    @xframe_options_exempt
    def getByPublishedUUID(self, request, published_uuid):
        app = get_object_or_404(App, published_uuid=published_uuid)
        owner_profile = get_object_or_404(Profile, user=app.owner)
        web_config = WebIntegrationConfig().from_dict(
            app.web_integration_config,
            owner_profile.decrypt_value,
        ) if app.web_integration_config else None

        # Only return the app if it is published and public or if the user is logged in and the owner
        if app.is_published:
            if app.owner == request.user or \
                    (app.visibility == AppVisibility.PUBLIC or app.visibility == AppVisibility.UNLISTED) or \
                (
                        request.user.is_authenticated and ((app.visibility == AppVisibility.ORGANIZATION and Profile.objects.get(user=app.owner).organization == Profile.objects.get(user=request.user).organization) or
                                                           (app.visibility == AppVisibility.PRIVATE and request.user.email in app.accessible_by))
                    ):
                serializer = AppSerializer(
                    instance=app, request_user=request.user,
                )
                csp = 'frame-ancestors *'
                if web_config and 'allowed_sites' in web_config and len(web_config['allowed_sites']) > 0 and any(web_config['allowed_sites']):
                    csp = 'frame-ancestors ' + \
                        ' '.join(
                            list(
                                filter(
                                    lambda x: x != '' and x !=
                                    None, web_config['allowed_sites'],
                                ),
                            ),
                        )
                return DRFResponse(data=serializer.data, status=200, headers={'Content-Security-Policy': csp})

        if app.visibility == AppVisibility.ORGANIZATION:
            return DRFResponse(status=403, data={'message': 'Please login to your organization account to access this app.'})
        elif app.visibility == AppVisibility.PRIVATE and request.user.is_anonymous:
            return DRFResponse(status=403, data={'message': 'Please login to access this app.'})
        else:
            return DRFResponse(status=404, data={'message': 'Nothing found here. Please check our app hub for more apps.'})

    def getCloneableApps(self, request, uid=None):
        json_data = None
        if uid:
            object = get_object_or_404(
                App, uuid=uuid.UUID(uid), is_cloneable=True,
            )
            serializer = CloneableAppSerializer(instance=object)
            json_data = serializer.data
            json_data['processors'] = self.get_processors_from_run_graph(
                json_data['run_graph'],
            )
            del json_data['run_graph']
        else:
            queryset = App.objects.all().filter(is_cloneable=True)
            serializer = CloneableAppSerializer(queryset, many=True)
            json_data = serializer.data
            for app in json_data:
                app['processors'] = self.get_processors_from_run_graph(
                    app['run_graph'],
                )
                del app['run_graph']
        return DRFResponse(json_data)

    def getTemplates(self, request, slug=None):
        json_data = None
        if slug:
            object = get_object_or_404(AppTemplate, slug=slug)
            serializer = AppTemplateSerializer(
                instance=object, context={'hide_details': False},
            )
            json_data = serializer.data
        else:
            queryset = AppTemplate.objects.all().order_by('order')
            serializer = AppTemplateSerializer(queryset, many=True)
            json_data = serializer.data
        return DRFResponse(json_data)

    def publish(self, request, uid):
        app = get_object_or_404(App, uuid=uuid.UUID(uid))
        if app.owner != request.user:
            return DRFResponse(status=403)

        if 'visibility' in request.data:
            if request.data['visibility'] == 3 and flag_enabled('CAN_PUBLISH_PUBLIC_APPS', request=request):
                app.visibility = AppVisibility.PUBLIC
            elif request.data['visibility'] == 2 and flag_enabled('CAN_PUBLISH_UNLISTED_APPS', request=request):
                app.visibility = AppVisibility.UNLISTED
            elif request.data['visibility'] == 1 and flag_enabled('CAN_PUBLISH_ORG_APPS', request=request):
                app.visibility = AppVisibility.ORGANIZATION
            elif request.data['visibility'] == 0 and (flag_enabled('CAN_PUBLISH_PRIVATE_APPS', request=request) or app.visibility == AppVisibility.PRIVATE):
                app.visibility = AppVisibility.PRIVATE
                if 'accessible_by' in request.data:
                    # Filter out invalid email addresses from accessible_by
                    valid_emails = []
                    for email in request.data['accessible_by']:
                        try:
                            validate_email(email)
                            valid_emails.append(email)
                        except ValidationError:
                            pass

                    # Only allow a maximum of 20 users to be shared with. Trim the list if it is more than 20
                    if len(valid_emails) > 20:
                        valid_emails = valid_emails[:20]

                    new_emails = list(
                        set(valid_emails) -
                        set(app.accessible_by),
                    )
                    app.accessible_by = valid_emails
                    app.access_permission = request.data[
                        'access_permission'
                    ] if 'access_permission' in request.data else AppAccessPermission.READ

                    # Send email to new users
                    # TODO: Use multisend to send emails in bulk
                    for new_email in new_emails:
                        email_template_cls = EmailTemplateFactory.get_template_by_name(
                            'app_shared'
                        )
                        share_email = email_template_cls(
                            uuid=app.uuid, published_uuid=app.published_uuid, app_name=app.name, owner_first_name=app.owner.first_name, owner_email=app.owner.email, can_edit=app.access_permission == AppAccessPermission.WRITE, share_to=new_email
                        )
                        share_email_sender = EmailSender(share_email)
                        share_email_sender.send()

        app_newly_published = not app.is_published
        app.is_published = True
        app.save()

        # Send app published email if the app was not published before
        if app_newly_published:
            email_template_cls = EmailTemplateFactory.get_template_by_name(
                'app_published'
            )
            app_published_email = email_template_cls(
                app_name=app.name, owner_first_name=app.owner.first_name, owner_email=app.owner.email, published_uuid=app.published_uuid)
            published_email_sender = EmailSender(app_published_email)
            published_email_sender.send()

        return DRFResponse(status=200)

    def unpublish(self, request, uid):
        app = get_object_or_404(App, uuid=uuid.UUID(uid))
        if app.owner != request.user:
            return DRFResponse(status=403)

        app.is_published = False
        app.save()

        return DRFResponse(status=200)

    def delete(self, request, uid):
        app = get_object_or_404(App, uuid=uuid.UUID(uid))
        if app.is_published:
            return DRFResponse(status=500, errors={'message': 'Cannot delete a published app.'})

        if app.owner != request.user:
            return DRFResponse(status=404)

        # Cleanup app run_graph
        run_graph_entries = app.run_graph.all()
        endpoint_entries = filter(lambda x: x != None, set(list(map(lambda x: x.entry_endpoint, run_graph_entries)) +
                                                           list(map(lambda x: x.exit_endpoint, run_graph_entries))))

        # Delete all the endpoint entries
        for entry in endpoint_entries:
            EndpointViewSet.delete(self, request, id=str(
                entry.parent_uuid), force_delete_app=True)

        # Delete all the run_graph entries
        for entry in run_graph_entries:
            entry.delete()

        app.delete()

        return DRFResponse(status=200)

    def patch(self, request, uid):
        app = get_object_or_404(App, uuid=uuid.UUID(uid))
        app_owner_profile = get_object_or_404(Profile, user=app.owner)
        if app.owner != request.user and not (
            app.visibility == AppVisibility.PRIVATE
            and app.access_permission == AppAccessPermission.WRITE
            and request.user.email in app.accessible_by
        ):
            return DRFResponse(status=403)

        app.name = request.data['name']
        app.description = request.data['description']
        app.config = request.data['config']
        app.input_schema = request.data['input_schema']
        app.input_ui_schema = request.data['input_ui_schema'] if 'input_ui_schema' in request.data else {
        }
        app.output_template = request.data['output_template'] if 'output_template' in request.data else {
        }
        app.data_transformer = request.data['data_transformer'] if 'data_transformer' in request.data else ''
        app.web_integration_config = WebIntegrationConfig(**request.data['web_config']).to_dict(
            app_owner_profile.encrypt_value,
        ) if 'web_config' in request.data and request.data['web_config'] else {}
        app.slack_integration_config = SlackIntegrationConfig(**request.data['slack_config']).to_dict(
            app_owner_profile.encrypt_value,
        ) if 'slack_config' in request.data and request.data['slack_config'] else {}
        app.discord_integration_config = DiscordIntegrationConfig(**request.data['discord_config']).to_dict(
            app_owner_profile.encrypt_value,
        ) if 'discord_config' in request.data and request.data['discord_config'] else {}
        processors = request.data['processors']
        endpoints = []
        graph_edges = []

        # Redo the graph edges
        for processor in processors:
            existing_endpoint = Endpoint.objects.filter(
                uuid=processor['endpoint'],
            ).first() if 'endpoint' in processor else None

            if existing_endpoint and existing_endpoint.input == processor['input'] and existing_endpoint.config == processor['config']:
                endpoints.append(existing_endpoint)
                continue

            api_backend_obj = get_object_or_404(
                ApiBackend, id=processor['api_backend'],
            )
            endpoint = Endpoint.objects.create(
                name=f'{app.name}:{api_backend_obj.name}',
                owner=app.owner,
                api_backend=api_backend_obj,
                draft=False,
                is_live=True,
                is_app=True,
                parent_uuid=existing_endpoint.parent_uuid if existing_endpoint else None,
                input=processor['input'] if 'input' in processor else {},
                config=processor['config'] if 'config' in processor else {},
                version=existing_endpoint.version + 1 if existing_endpoint else 0,
            )
            endpoints.append(endpoint)

        # First edge is from the app input to the first endpoint
        if len(endpoints) > 0:
            edge = AppRunGraphEntry.objects.create(
                owner=app.owner,
                entry_endpoint=None,
                exit_endpoint=endpoints[0],
                data_transformer=app.data_transformer,
            )
            edge.save()
            graph_edges.append(edge)

        for i in range(len(endpoints)):
            if i == len(endpoints) - 1:
                break
            edge = AppRunGraphEntry.objects.create(
                owner=app.owner,
                entry_endpoint=endpoints[i],
                exit_endpoint=endpoints[i+1],
                data_transformer='',
            )
            edge.save()
            graph_edges.append(edge)

        # Add the last edge from the last endpoint to the app output
        if len(endpoints) > 0:
            edge = AppRunGraphEntry.objects.create(
                owner=app.owner,
                entry_endpoint=endpoints[-1],
                exit_endpoint=None,
                data_transformer='',
            )
            edge.save()
            graph_edges.append(edge)

        app.run_graph.set(graph_edges)
        app.last_modified_by = request.user
        app.save()

        return DRFResponse(AppSerializer(instance=app, request_user=request.user).data, status=201)

    def post(self, request):
        owner = request.user
        app_type = get_object_or_404(AppType, id=request.data['app_type'])
        app_name = request.data['name']
        app_description = request.data['description'] if 'description' in request.data else ''
        app_config = request.data['config'] if 'config' in request.data else {}
        app_input_schema = request.data['input_schema']
        app_input_ui_schema = request.data['input_ui_schema'] if 'input_ui_schema' in request.data else {
        }
        app_output_template = request.data['output_template'] if 'output_template' in request.data else {
        }
        app_data_transformer = request.data['data_transformer'] if 'data_transformer' in request.data else ''
        processors = request.data['processors']
        endpoints = []
        graph_edges = []

        # Iterate over processors and create an endpoint for each using api_backend
        # and then use that to create AppRunGraphEntry to create the graph
        for processor in processors:
            api_backend_obj = get_object_or_404(
                ApiBackend, id=processor['api_backend'],
            )
            endpoint = Endpoint.objects.create(
                name=f'{app_name}:{api_backend_obj.name}',
                owner=owner,
                api_backend=api_backend_obj,
                draft=False,
                is_live=True,
                is_app=True,
                parent_uuid=None,
                input=processor['input'] if 'input' in processor else {},
                config=processor['config'] if 'config' in processor else {},
            )
            endpoints.append(endpoint)

        # First edge is from the app input to the first endpoint
        if len(endpoints) > 0:
            edge = AppRunGraphEntry.objects.create(
                owner=owner,
                entry_endpoint=None,
                exit_endpoint=endpoints[0],
                data_transformer=app_data_transformer,
            )
            edge.save()
            graph_edges.append(edge)

        for i in range(len(endpoints)):
            if i == len(endpoints) - 1:
                break
            edge = AppRunGraphEntry.objects.create(
                owner=owner,
                entry_endpoint=endpoints[i],
                exit_endpoint=endpoints[i+1],
                data_transformer='',
            )
            edge.save()
            graph_edges.append(edge)

        # Add the last edge from the last endpoint to the app output
        if len(endpoints) > 0:
            edge = AppRunGraphEntry.objects.create(
                owner=owner,
                entry_endpoint=endpoints[-1],
                exit_endpoint=None,
                data_transformer='',
            )
            edge.save()
            graph_edges.append(edge)

        template = AppTemplate.objects.filter(
            slug=request.data['template_slug'],
        ).first() if 'template_slug' in request.data else None

        app = App.objects.create(
            name=app_name,
            owner=owner,
            description=app_description,
            type=app_type,
            config=app_config,
            input_schema=app_input_schema,
            input_ui_schema=app_input_ui_schema,
            output_template=app_output_template,
            data_transformer=app_data_transformer,
            template=template,
        )
        app.run_graph.set(graph_edges)
        app.save()

        return DRFResponse(AppSerializer(instance=app).data, status=201)

    @action(detail=True, methods=['post'])
    @xframe_options_exempt
    def run(self, request, uid, session_id=None, platform=None):
        stream = request.data.get('stream', False)
        request_uuid = str(uuid.uuid4())
        try:
            result = self.run_app_internal(
                uid, session_id, request_uuid, request, platform,
            )
            if stream:
                response = StreamingHttpResponse(
                    streaming_content=result, content_type='application/json',
                )
                response.is_async = True
                return response
            response_body = {k: v for k, v in result.items() if k != 'csp'}
            response_body['_id'] = request_uuid
            return DRFResponse(response_body, status=200, headers={'Content-Security-Policy': result['csp'] if 'csp' in result else 'frame-ancestors self'})
        except AppRunnerException as e:
            logger.exception('Error while running app')
            return DRFResponse({'errors': [str(e)]}, status=e.status_code)
        except Exception as e:
            logger.exception('Error while running app')
            return DRFResponse({'errors': [str(e)]}, status=400)

    async def run_app_internal_async(self, uid, session_id, request_uuid, request):
        return await database_sync_to_async(self.run_app_internal)(uid, session_id, request_uuid, request)

    def run_app_internal(self, uid, session_id, request_uuid, request, platform=None):
        app = get_object_or_404(App, uuid=uuid.UUID(uid))
        app_owner = get_object_or_404(Profile, user=app.owner)

        app_runner_class = None
        if platform == 'discord':
            app_runner_class = AppRunerFactory.get_app_runner('discord')
        elif platform == 'slack':
            app_runner_class = AppRunerFactory.get_app_runner('slack')
        else:
            app_runner_class = AppRunerFactory.get_app_runner(app.type.slug)

        app_runner = app_runner_class(
            app=app, request_uuid=request_uuid, request=request, session_id=session_id, app_owner=app_owner,
        )

        return app_runner.run_app()

    @action(detail=True, methods=['post'])
    def run_discord(self, request, uid):
        return self.run(request, uid, platform='discord')

    @action(detail=True, methods=['post'])
    def run_slack(self, request, uid):
        return self.run(request, uid, platform='slack')

    def testsets(self, request, uid):
        app = get_object_or_404(App, uuid=uuid.UUID(uid))
        if app.owner != request.user:
            return DRFResponse(status=404)
        test_set = AppTestSetViewSet()

        if request.method == 'GET':
            testsets = TestSet.objects.filter(app=app)
            return DRFResponse(
                list(
                    map(
                        lambda x: test_set.get(
                            request, str(x.uuid),
                        ).data, testsets,
                    ),
                ),
            )
        elif request.method == 'POST':

            return test_set.post(request, app)
        return DRFResponse(status=405)


class AppHubViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    # @method_decorator(cache_page(60*60*24))
    def list(self, request):
        apphub_objs = AppHub.objects.all().order_by('rank')

        return DRFResponse(AppHubSerializer(instance=apphub_objs, many=True).data)


class AppTestCasesViewSet(viewsets.ViewSet):
    def get(self, request, uid=None):
        if uid:
            testcase = get_object_or_404(TestCase, uuid=uuid.UUID(uid))
            if testcase.testset.app.owner != request.user:
                return DRFResponse(status=403)

            return DRFResponse(TestCaseSerializer(instance=testcase).data)

        return DRFResponse(status=405)

    def delete(self, request, uid):
        testcase = get_object_or_404(TestCase, uuid=uuid.UUID(uid))
        if testcase.testset.app.owner != request.user:
            return DRFResponse(status=403)

        testcase.delete()
        return DRFResponse(status=204)


class AppTestSetViewSet(viewsets.ModelViewSet):

    def get(self, request, uid=None):
        testset = get_object_or_404(TestSet, uuid=uuid.UUID(uid))
        testcases = self.getTestCases(request, uid)
        response = TestSetSerializer(instance=testset).data
        response['testcases'] = testcases.data
        return DRFResponse(response)

    def getTestCases(self, request, uid):
        testset = get_object_or_404(TestSet, uuid=uuid.UUID(uid))
        if testset.app.owner != request.user:
            return DRFResponse(status=403)

        testcases = TestCase.objects.filter(testset=testset)
        return DRFResponse(TestCaseSerializer(instance=testcases, many=True).data)

    def post(self, request, app):
        testset_name = request.data['name']

        testset = TestSet.objects.create(name=testset_name, app=app)

        return DRFResponse(TestSetSerializer(instance=testset).data, status=201)

    def delete(self, request, uid):
        testset = get_object_or_404(TestSet, uuid=uuid.UUID(uid))
        if request.user != testset.app.owner:
            return DRFResponse(status=403)
        testset.delete()
        return DRFResponse(status=204)

    def add_entry(self, request, uid):
        testset = get_object_or_404(TestSet, uuid=uuid.UUID(uid))
        if request.user != testset.app.owner:
            return DRFResponse(status=403)

        testcase = TestCase.objects.create(
            testset=testset,
            input_data=request.data['input_data'], expected_output=request.data[
                'expected_output'] if 'expected_output' in request.data else '',
        )

        return DRFResponse(TestCaseSerializer(instance=testcase).data, status=201)
