import asyncio
import json
import logging
import uuid
from collections import namedtuple

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.db.models import Max
from django.http import (
    Http404,
    HttpResponseForbidden,
    HttpResponseNotFound,
    StreamingHttpResponse,
)
from django.views.decorators.csrf import csrf_exempt
from flags.state import flag_enabled
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response as DRFResponse
from rest_framework.views import APIView

from llmstack.apps.app_session_utils import create_app_session
from llmstack.apps.models import App
from llmstack.base.models import Profile, get_vendor_env_platform_defaults
from llmstack.play.actor import ActorConfig
from llmstack.play.actors.bookkeeping import BookKeepingActor
from llmstack.play.actors.input import InputActor, InputRequest
from llmstack.play.actors.output import OutputActor
from llmstack.play.coordinator import Coordinator
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface

from .models import Endpoint, RunEntry
from .providers.api_processors import ApiProcessorFactory
from .serializers import HistorySerializer, LoginSerializer

Schema = namedtuple("Schema", "type default is_required")

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
        # If the object is a string, replace double quotes with escaped double
        # quotes
        json_obj = json_obj.replace('"', '\\"')
    return json_obj


class EndpointViewSet(viewsets.ViewSet):
    @action(detail=True, methods=["post"])
    @csrf_exempt
    def invoke_api(self, request, id, version=None):
        # If version is not provided, find latest live endpoint
        endpoint = None
        if version is None:
            endpoint = (
                Endpoint.objects.filter(
                    parent_uuid=uuid.UUID(
                        id,
                    ),
                    is_live=True,
                )
                .order_by("-version")
                .first()
            )
        else:
            endpoint = Endpoint.objects.filter(
                parent_uuid=uuid.UUID(id),
                version=version,
            ).first()

        # Couldn't find a live version. Find latest version for endpoint
        if not endpoint:
            endpoint = (
                Endpoint.objects.filter(
                    parent_uuid=uuid.UUID(id),
                )
                .order_by("-version")
                .first()
            )

        if not endpoint:
            return HttpResponseNotFound("Invalid endpoint")

        if request.user != endpoint.owner:
            return HttpResponseForbidden("Invalid ownership")

        bypass_cache = request.data.get("bypass_cache", False)

        # Create request object for this versioned endpoint
        template_values = request.data["template_values"] if "template_values" in request.data else {}
        config = request.data["config"] if "config" in request.data else {}
        input = request.data["input"] if "input" in request.data else {}

        stream = request.data.get("stream", False)

        request_user_agent = request.META.get(
            "HTTP_USER_AGENT",
            "Streaming API Client" if stream else "API Client",
        )
        request_location = request.headers.get("X-Client-Geo-Location", "")
        request_ip = request_ip = request.headers.get(
            "X-Forwarded-For",
            request.META.get(
                "REMOTE_ADDR",
                "",
            ),
        ).split(
            ",",
        )[0].strip() or request.META.get("HTTP_X_REAL_IP", "")

        request_user_email = ""
        if request.user and request.user.email and len(request.user.email) > 0:
            request_user_email = request.user.email
        elif request.user and request.user.username and len(request.user.username) > 0:
            # Use username as email if email is not set
            request_user_email = request.user.username

        input_request = InputRequest(
            request_endpoint_uuid=str(
                endpoint.uuid,
            ),
            request_app_uuid="",
            request_app_session_key="",
            request_owner=request.user,
            request_uuid=str(
                uuid.uuid4(),
            ),
            request_user_email=request_user_email,
            request_ip=request_ip,
            request_location=request_location,
            request_user_agent=request_user_agent,
            request_body=request.data,
            request_content_type=request.content_type,
        )
        try:
            invoke_result = self.run_endpoint(
                endpoint_uuid=endpoint.uuid,
                run_as_user=request.user,
                input_request=input_request,
                template_values=template_values,
                bypass_cache=bypass_cache,
                input={
                    **endpoint.input,
                    **input,
                },
                config={
                    **endpoint.config,
                    **config,
                },
                api_backend_slug=endpoint.api_backend.slug,
                api_provider_slug=endpoint.api_backend.api_provider.slug,
                app_session=None,
                stream=stream,
            )

            if stream:
                response = StreamingHttpResponse(
                    streaming_content=invoke_result,
                    content_type="application/json",
                )
                response.is_async = True
                return response
        except Exception as e:
            invoke_result = {"id": -1, "errors": [str(e)]}

        if "errors" in invoke_result:
            return DRFResponse({"errors": invoke_result["errors"]}, status=500)

        return DRFResponse(invoke_result)

    def run(self, request):
        request_uuid = str(uuid.uuid4())

        bypass_cache = request.data.get("bypass_cache", False)
        config = request.data["config"] if "config" in request.data else {}
        input = request.data["input"] if "input" in request.data else {}
        stream = False

        api_backend_slug = request.data.get("api_backend_slug", None)
        api_provider_slug = request.data.get("api_provider_slug", None)

        if api_backend_slug is None or api_provider_slug is None:
            return DRFResponse({"errors": ["Invalid API backend"]}, status=500)

        request_user_agent = request.META.get(
            "HTTP_USER_AGENT",
            "Streaming API Client" if stream else "API Client",
        )
        request_location = request.headers.get("X-Client-Geo-Location", "")
        request_ip = request_ip = request.headers.get(
            "X-Forwarded-For",
            request.META.get(
                "REMOTE_ADDR",
                "",
            ),
        ).split(
            ",",
        )[0].strip() or request.META.get("HTTP_X_REAL_IP", "")

        request_owner = None if request.user.is_anonymous else request.user
        request_user_email = "" if request.user.is_anonymous else request.user.email

        input_request = InputRequest(
            request_endpoint_uuid=request_uuid,
            request_app_uuid="",
            request_app_session_key="",
            request_owner=request_owner,
            request_uuid=str(
                uuid.uuid4(),
            ),
            request_user_email=request_user_email,
            request_ip=request_ip,
            request_location=request_location,
            request_user_agent=request_user_agent,
            request_body=request.data,
            request_content_type=request.content_type,
        )

        try:
            invoke_result = self.run_endpoint(
                endpoint_uuid=request_uuid,
                run_as_user=request_owner,
                input_request=input_request,
                template_values={},
                bypass_cache=bypass_cache,
                input={
                    **input,
                },
                config={
                    **config,
                },
                api_backend_slug=api_backend_slug,
                api_provider_slug=api_provider_slug,
                app_session=None,
                stream=False,
            )
        except Exception as e:
            invoke_result = {"id": -1, "errors": [str(e)]}

        if "errors" in invoke_result:
            return DRFResponse({"errors": invoke_result["errors"]}, status=500)

        return DRFResponse(invoke_result)

    def run_endpoint(
        self,
        endpoint_uuid,
        run_as_user,
        input_request,
        template_values={},
        bypass_cache=False,
        input={},
        config={},
        api_backend_slug="",
        api_provider_slug="",
        app_session=None,
        output_stream=None,
        stream=False,
    ):
        profile = Profile.objects.get(user=run_as_user) if run_as_user else None

        vendor_env = profile.get_vendor_env() if profile else get_vendor_env_platform_defaults()

        # Pick a processor
        processor_cls = ApiProcessorFactory.get_api_processor(
            api_backend_slug,
            api_provider_slug,
        )

        if not app_session:
            app_session = create_app_session(None, str(uuid.uuid4()))

        app_session_data = None

        actor_configs = [
            ActorConfig(
                name=str(endpoint_uuid),
                template_key="processor",
                actor=processor_cls,
                dependencies=["input"],
                kwargs={
                    "config": config,
                    "input": input,
                    "env": vendor_env,
                    "session_data": app_session_data["data"] if app_session_data and "data" in app_session_data else {},
                },
                output_cls=processor_cls.get_output_cls(),
            ),
            ActorConfig(
                name="input",
                template_key="input",
                actor=InputActor,
                kwargs={
                    "input_request": input_request,
                },
            ),
            ActorConfig(
                name="output",
                template_key="output",
                actor=OutputActor,
                dependencies=["processor"],
                kwargs={
                    "template": "{{ processor | tojson }}",
                },
            ),
            ActorConfig(
                name="bookkeeping",
                template_key="bookkeeping",
                actor=BookKeepingActor,
                dependencies=[
                    "input",
                    "output",
                ],
                kwargs={
                    "processor_configs": {
                        str(endpoint_uuid): {
                            "processor": {
                                "uuid": str(endpoint_uuid),
                            },
                            "app_session": None,
                            "app_session_data": None,
                            "template_key": "processor",
                        },
                    },
                },
            ),
        ]

        try:
            coordinator_ref = Coordinator.start(
                session_id=app_session["uuid"],
                actor_configs=actor_configs,
            )
            coordinator = coordinator_ref.proxy()

            output = None
            input_actor = coordinator.get_actor("input").get().proxy()
            output_actor = coordinator.get_actor("output").get().proxy()
            output_iter = None
            if input_actor and output_actor:
                input_actor.write(template_values).get()
                output_iter = output_actor.get_output().get() if not stream else output_actor.get_output_stream().get()

            if stream:
                # Return a wrapper over output_iter where we call next() on
                # output_iter and yield the result
                async def stream_output():
                    try:
                        while True:
                            await asyncio.sleep(0.0001)
                            output = next(output_iter)
                            yield {"output": output["processor"]}
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

        except Exception as e:
            logger.exception(e)
            raise Exception(f"Error starting coordinator: {e}")

        if isinstance(output, dict) and "errors" in output:
            return output
        else:
            return {"output": json.loads(output)}


class ApiProviderViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def list(self, request):
        processor_providers = list(
            filter(
                lambda provider: provider.get(
                    "processor_packages",
                ),
                settings.PROVIDERS,
            ),
        )
        data = list(
            map(
                lambda provider: {
                    "name": provider.get("name"),
                    "slug": provider.get("slug"),
                },
                processor_providers,
            ),
        )

        return DRFResponse(data)


class ApiBackendViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def get(self, request, id):
        api_backends = self.list(request).data
        for api_backend in api_backends:
            if api_backend["id"] == id:
                return DRFResponse(api_backend)
        return DRFResponse(status=404)

    def list(self, request):
        providers = ApiProviderViewSet().list(request).data
        providers_map = {}
        for entry in providers:
            providers_map[entry["slug"]] = entry
        processors = []
        for subclass in ApiProcessorInterface.__subclasses__():
            if f"{subclass.__module__}.{subclass.__qualname__}" in settings.PROCESSOR_EXCLUDE_LIST:
                continue

            if subclass.provider_slug() not in providers_map:
                continue

            try:
                processor_name = subclass.name()
            except NotImplementedError:
                processor_name = subclass.slug().capitalize()

            processors.append(
                {
                    "id": f"{subclass.provider_slug()}/{subclass.slug()}",
                    "name": processor_name,
                    "slug": subclass.slug(),
                    "api_provider": providers_map[subclass.provider_slug()],
                    "api_endpoint": {},
                    "params": {},
                    "description": subclass.description(),
                    "input_schema": json.loads(subclass.get_input_schema()),
                    "output_schema": json.loads(subclass.get_output_schema()),
                    "config_schema": json.loads(subclass.get_configuration_schema()),
                    "input_ui_schema": subclass.get_input_ui_schema(),
                    "output_ui_schema": subclass.get_output_ui_schema(),
                    "config_ui_schema": subclass.get_configuration_ui_schema(),
                    "output_template": (
                        subclass.get_output_template().dict() if subclass.get_output_template() else None
                    ),
                },
            )
        return DRFResponse(processors)


class HistoryViewSet(viewsets.ModelViewSet):
    paginate_by = 20
    permission_classes = [IsAuthenticated]

    def list(self, request):
        app_uuid = request.GET.get("app_uuid", None)
        session_key = request.GET.get("session_key", None)
        request_user_email = request.GET.get("request_user_email", None)
        endpoint_uuid = request.GET.get("endpoint_uuid", None)
        detail = request.GET.get("detail", False)

        filters = {}
        if app_uuid and app_uuid != "null":
            app = App.objects.filter(uuid=app_uuid).first()
            if app and app.has_write_permission(request.user):
                filters["app_uuid"] = app_uuid
                filters["owner"] = app.owner

        if session_key and session_key != "null":
            filters["session_key"] = session_key
        if request_user_email and request_user_email != "null":
            filters["request_user_email"] = request_user_email
        if endpoint_uuid and endpoint_uuid != "null":
            filters["endpoint_uuid"] = endpoint_uuid

        if not filters:
            filters["owner"] = request.user

        queryset = RunEntry.objects.all().filter(**filters).order_by("-created_at")
        page = self.paginate_queryset(queryset)
        if page is not None:
            response = self.get_paginated_response(
                HistorySerializer(
                    page,
                    many=True,
                    context={
                        "hide_details": not detail,
                    },
                ).data,
            )
        else:
            response = HistorySerializer(
                queryset,
                many=True,
                context={"hide_details": not detail},
            )

        return DRFResponse(response.data)

    def get_csv(self, queryset, brief):
        header = ["Created At", "Session", "Request", "Response"]
        if not brief:
            header.extend(
                [
                    "Request UUID",
                    "Request User Email",
                    "Request IP",
                    "Request Location",
                    "Request User Agent",
                    "Request Content Type",
                ],
            )
        yield ",".join(header) + "\n"
        for entry in queryset:
            output = [
                entry.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                entry.session_key if entry.session_key else "",
                json.dumps(
                    entry.request_body,
                ),
                json.dumps(
                    entry.response_body,
                ),
            ]
            if not brief:
                output.extend(
                    [
                        entry.request_uuid,
                        entry.request_user_email,
                        entry.request_ip,
                        entry.request_location,
                        entry.request_user_agent,
                        entry.request_content_type,
                    ],
                )
            yield ",".join(output) + "\n"

    def download(self, request):
        if not flag_enabled("CAN_EXPORT_HISTORY", request=request):
            return HttpResponseForbidden(
                "You do not have permission to download history",
            )

        app_uuid = request.data.get("app_uuid", None)
        before = request.data.get("before", None)
        count = request.data.get("count", 25)
        brief = request.data.get("brief", True)

        if count > 100:
            count = 100

        queryset = (
            RunEntry.objects.all()
            .filter(
                app_uuid=app_uuid,
                owner=request.user,
                created_at__lt=before,
            )
            .order_by("-created_at")[:count]
        )
        response = StreamingHttpResponse(
            streaming_content=self.get_csv(
                queryset,
                brief,
            ),
            content_type="text/csv",
        )
        response["Content-Disposition"] = f'attachment; filename="history_{app_uuid}_{before}_{count}.csv"'
        return response

    def list_sessions(self, request):
        app_uuid = request.GET.get("app_uuid", None)
        filters = {
            "owner": request.user,
            "session_key__isnull": False,
        }

        if app_uuid and app_uuid != "null":
            filters["app_uuid"] = app_uuid

        queryset = (
            RunEntry.objects.all()
            .filter(
                **filters,
            )
            .values(
                "session_key",
                "app_uuid",
                "request_user_email",
                "platform_data",
            )
            .annotate(
                latest_created_at=Max("created_at"),
            )
            .order_by("-latest_created_at")
            .distinct()
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            response = self.get_paginated_response(page)
        else:
            response = queryset
        return DRFResponse(response.data)

    def get(self, request, request_uuid):
        object = (
            RunEntry.objects.all()
            .filter(
                request_uuid=request_uuid,
                owner=request.user,
            )
            .first()
        )
        if not object:
            raise Http404("Invalid request uuid")

        return DRFResponse(HistorySerializer(instance=object).data)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.data.get("username")
            password = serializer.data.get("password")
            user = authenticate(username=username, password=password)
            if user:
                login(request=request, user=user)
                return DRFResponse({"message": "Login successful"})

        return DRFResponse(
            "Error in signing in",
            status=status.HTTP_400_BAD_REQUEST,
        )


class LogoutAPIView(APIView):
    def post(self, request):
        logout(request)
        return DRFResponse({"message": "Logout successful"})
