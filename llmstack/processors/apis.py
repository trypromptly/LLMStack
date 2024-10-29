import json
import logging
from collections import namedtuple

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.db.models import Max, Q
from django.http import HttpResponseForbidden, StreamingHttpResponse
from django.views.decorators.cache import cache_page
from flags.state import flag_enabled
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response as DRFResponse
from rest_framework.views import APIView

from llmstack.apps.models import App
from llmstack.common.utils.provider_config import (
    get_provider_config_class_by_slug_cached,
)
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface

from .models import Feedback, RunEntry
from .serializers import HistorySerializer, LoginSerializer

Schema = namedtuple("Schema", "type default is_required")

logger = logging.getLogger(__name__)


class ApiProviderViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    method = ["GET"]

    @cache_page(60 * 60 * 12)
    def list(self, request):
        data = []
        for provider in settings.PROVIDERS:
            provider_config_cls = get_provider_config_class_by_slug_cached(provider.get("slug"))
            data.append(
                {
                    "name": provider.get("name"),
                    "slug": provider.get("slug"),
                    "has_processors": bool(
                        provider.get(
                            "processor_packages",
                        ),
                    ),
                    "config_schema": provider_config_cls.get_config_schema() if provider_config_cls else None,
                    "config_ui_schema": provider_config_cls.get_config_ui_schema() if provider_config_cls else None,
                },
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

            for entry in subclass.api_backends():
                entry["provider"] = providers_map[entry["provider_slug"]]
                processors.append(entry)

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

        if filters:
            queryset = RunEntry.objects.all().filter(**filters).order_by("-created_at")
        else:
            queryset = (
                RunEntry.objects.all()
                .filter(Q(owner=request.user) | Q(request_user_email=request.user.email))
                .order_by("-created_at")
            )
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
                    "Response Quality",
                    "Response Feedback",
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
                feedback = entry.feedback
                output.extend(
                    [
                        entry.request_uuid,
                        entry.request_user_email,
                        entry.request_ip,
                        entry.request_location,
                        entry.request_user_agent,
                        entry.request_content_type,
                        feedback.response_quality if feedback else "",
                        feedback.response_feedback if feedback else "",
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
        app = App.objects.filter(uuid=app_uuid).first()
        if not app or not app.has_write_permission(request.user):
            return DRFResponse(status=403)

        filters = {
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
        object = RunEntry.objects.get(request_uuid=request_uuid)

        if object.request_user_email == request.user.email:
            return DRFResponse(HistorySerializer(instance=object).data)

        if object.owner == request.user:
            return DRFResponse(HistorySerializer(instance=object).data)

        if object.platform_data:
            if object.platform_data.get("type") in ["slack", "twilio", "discord", "web", "api"]:
                app_uuid = object.app_uuid
                app = App.objects.filter(uuid=app_uuid).first()
                if app:
                    if app.has_write_permission(request.user):
                        return DRFResponse(HistorySerializer(instance=object).data)

        return DRFResponse(status=403)

    def patch(self, request, request_uuid):
        run_entry = RunEntry.objects.filter(request_uuid=request_uuid, owner=request.user).first()
        if "feedback" in request.data:
            response_quality = request.data.get("feedback").get("response_quality")
            response_feedback = request.data.get("feedback").get("response_feedback")
            Feedback.objects.create(
                request_uuid=run_entry.request_uuid,
                response_quality=response_quality,
                response_feedback=response_feedback,
            )
            return DRFResponse(status=status.HTTP_201_CREATED)

        return DRFResponse(status=status.HTTP_400_BAD_REQUEST)


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
