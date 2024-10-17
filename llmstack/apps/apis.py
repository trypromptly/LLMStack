import json
import logging
import os
import uuid

import yaml
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from django.conf import settings
from django.core.validators import validate_email
from django.db.models import Q
from django.forms import ValidationError
from django.http import StreamingHttpResponse
from django.shortcuts import aget_object_or_404, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.clickjacking import xframe_options_exempt
from drf_yaml.parsers import YAMLParser
from flags.state import flag_enabled
from pydantic import BaseModel
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response as DRFResponse

from llmstack.apps.app_session_utils import create_app_session
from llmstack.apps.integration_configs import (
    DiscordIntegrationConfig,
    SlackIntegrationConfig,
    TwilioIntegrationConfig,
    WebIntegrationConfig,
)
from llmstack.apps.runner.app_runner import AppRunner
from llmstack.apps.yaml_loader import (
    get_app_template_by_slug,
    get_app_templates_from_contrib,
)
from llmstack.base.models import AnonymousProfile, Profile
from llmstack.common.utils.utils import get_location
from llmstack.connections.apis import ConnectionsViewSet
from llmstack.emails.sender import EmailSender
from llmstack.emails.templates.factory import EmailTemplateFactory
from llmstack.processors.providers.processors import ProcessorFactory

from .models import App, AppData, AppHub, AppType, AppVisibility
from .serializers import (
    AppDataSerializer,
    AppHubSerializer,
    AppSerializer,
    AppTypeSerializer,
)

logger = logging.getLogger(__name__)


class AppOutputModel(BaseModel):
    output: dict


class AppRunnerException(Exception):
    status_code = 400
    details = None
    json_details = None


def get_connections(profile):
    from django.test import RequestFactory

    request = RequestFactory().get("/api/connections/")
    request.user = profile.user
    response = ConnectionsViewSet().list(request)
    return dict(map(lambda entry: (entry["id"], entry), response.data))


class AppTypeViewSet(viewsets.ViewSet):
    @method_decorator(cache_page(60 * 60 * 24))
    def get(self, request):
        queryset = AppType.objects.all()
        serializer = AppTypeSerializer(queryset, many=True)
        return DRFResponse(serializer.data)


class AppViewSet(viewsets.ViewSet):
    parser_classes = (JSONParser, FormParser, MultiPartParser, YAMLParser)

    def get_permissions(self):
        if (
            self.action == "getByPublishedUUID"
            or self.action == "run"
            or self.action == "run_slack"
            or self.action == "run_discord"
            or self.action == "run_twiliosms"
            or self.action == "run_twiliovoice"
        ):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, uid=None):
        fields = request.query_params.get("fields", None)
        if fields:
            fields = fields.split(",")

        if uid:
            app = get_object_or_404(
                App,
                uuid=uuid.UUID(uid),
            )
            if not app.has_read_permission(request.user):
                return DRFResponse(status=403)
            serializer = AppSerializer(
                instance=app,
                fields=fields,
                request_user=request.user,
            )
            return DRFResponse(serializer.data)

        queryset = App.objects.all().filter(owner=request.user).order_by("-created_at")
        serializer = AppSerializer(
            queryset,
            many=True,
            fields=fields,
            request_user=request.user,
        )
        return DRFResponse(serializer.data)

    def getShared(self, request):
        fields = request.query_params.get("fields", None)
        if fields:
            fields = fields.split(",")

        apps_queryset = App.objects.filter(
            Q(read_accessible_by__contains=[request.user.email])
            | Q(write_accessible_by__contains=[request.user.email]),
            is_published=True,
        ).order_by("-last_updated_at")

        organization = get_object_or_404(Profile, user=request.user).organization
        combined_queryset = apps_queryset

        if organization:
            org_apps_queryset = App.objects.filter(
                owner__in=Profile.objects.filter(organization=organization).values("user").exclude(user=request.user),
                visibility__gte=AppVisibility.ORGANIZATION,
                is_published=True,
            ).order_by("-last_updated_at")
            combined_queryset = list(apps_queryset) + list(org_apps_queryset)

        combined_serializer = AppSerializer(
            combined_queryset,
            many=True,
            fields=fields,
            request_user=request.user,
        )

        return DRFResponse(combined_serializer.data)

    def versions(self, request, uid=None, version=None):
        draft = request.query_params.get("draft", False)

        if not uid:
            return DRFResponse(status=400, data={"message": "uid is required"})

        app = get_object_or_404(
            App,
            uuid=uuid.UUID(uid),
        )

        if not app.has_read_permission(request.user):
            return DRFResponse(status=403)

        if version:
            versioned_app_data = AppData.objects.filter(
                app_uuid=app.uuid,
                version=version,
                is_draft=draft,
            ).first()
            if versioned_app_data:
                return DRFResponse(
                    AppDataSerializer(
                        versioned_app_data,
                        context={
                            "hide_details": False,
                        },
                    ).data,
                )
            else:
                return DRFResponse(
                    status=404,
                    data={
                        "message": "Version not found",
                    },
                )
        else:
            queryset = (
                AppData.objects.all()
                .filter(
                    app_uuid=app.uuid,
                )
                .order_by("-created_at")
            )
            serializer = AppDataSerializer(queryset, many=True)
            return DRFResponse(serializer.data)

    @xframe_options_exempt
    def getByPublishedUUID(self, request, published_uuid):
        app = get_object_or_404(App, published_uuid=published_uuid)
        owner_profile = get_object_or_404(Profile, user=app.owner)
        web_config = (
            WebIntegrationConfig().from_dict(
                app.web_integration_config,
                owner_profile.decrypt_value,
            )
            if app.web_integration_config
            else None
        )

        # Only return the app if it is published and public or if the user is
        # logged in and the owner
        if app.is_published:
            if (
                app.owner == request.user
                or (app.visibility == AppVisibility.PUBLIC or app.visibility == AppVisibility.UNLISTED)
                or (
                    request.user.is_authenticated
                    and (
                        (
                            app.visibility == AppVisibility.ORGANIZATION
                            and Profile.objects.get(
                                user=app.owner,
                            ).organization
                            == Profile.objects.get(
                                user=request.user,
                            ).organization
                        )
                        or (
                            request.user.email in app.read_accessible_by
                            or request.user.email in app.write_accessible_by
                        )
                    )
                )
            ):
                serializer = AppSerializer(
                    instance=app,
                    request_user=request.user,
                )
                csp = "frame-ancestors *"
                if (
                    web_config
                    and "allowed_sites" in web_config
                    and len(
                        web_config["allowed_sites"],
                    )
                    > 0
                    and any(
                        web_config["allowed_sites"],
                    )
                ):
                    csp = "frame-ancestors " + " ".join(
                        list(
                            filter(
                                lambda x: x != "" and x is not None,
                                web_config["allowed_sites"],
                            ),
                        ),
                    )
                return DRFResponse(
                    data=serializer.data,
                    status=200,
                    headers={
                        "Content-Security-Policy": csp,
                    },
                )

        if app.visibility == AppVisibility.ORGANIZATION:
            return DRFResponse(
                status=403,
                data={
                    "message": "Please login to your organization account to access this app.",
                },
            )
        elif app.visibility == AppVisibility.PRIVATE and request.user.is_anonymous:
            return DRFResponse(
                status=403,
                data={
                    "message": "Please login to access this app.",
                },
            )
        else:
            return DRFResponse(
                status=404,
                data={
                    "message": "Nothing found here. Please check our app hub for more apps.",
                },
            )

    def getTemplates(self, request, slug=None):
        json_data = None
        if slug:
            object = get_app_template_by_slug(slug)
            if object:
                object_dict = object.model_dump(exclude_none=True)
                # For backward compatibility with old app templates
                for page in object_dict["pages"]:
                    page["schema"] = page["input_schema"]
                    page["ui_schema"] = page["input_ui_schema"]
                json_data = object_dict
        else:
            json_data = []
            app_templates_from_yaml = get_app_templates_from_contrib()
            for app_template in app_templates_from_yaml:
                app_template_dict = app_template.model_dump()
                app_template_dict.pop("pages")
                app = app_template_dict.pop("app")
                json_data.append(
                    {
                        **app_template_dict,
                        **{"app": {"type_slug": app["type_slug"]}},
                    },
                )

        return DRFResponse(json_data)

    def publish(self, request, uid):
        app = get_object_or_404(App, uuid=uuid.UUID(uid))
        if not app.has_write_permission(request.user):
            return DRFResponse(status=403)

        if "visibility" in request.data:
            if request.data["visibility"] == 3 and flag_enabled(
                "CAN_PUBLISH_PUBLIC_APPS",
                request=request,
            ):
                app.visibility = AppVisibility.PUBLIC
            elif request.data["visibility"] == 2 and flag_enabled("CAN_PUBLISH_UNLISTED_APPS", request=request):
                app.visibility = AppVisibility.UNLISTED
            elif request.data["visibility"] == 1 and flag_enabled("CAN_PUBLISH_ORG_APPS", request=request):
                app.visibility = AppVisibility.ORGANIZATION
            elif request.data["visibility"] == 0 and (
                flag_enabled("CAN_PUBLISH_PRIVATE_APPS", request=request) or app.visibility == AppVisibility.PRIVATE
            ):
                app.visibility = AppVisibility.PRIVATE

        if (
            flag_enabled(
                "CAN_PUBLISH_PRIVATE_APPS",
                request=request,
            )
            or app.visibility == AppVisibility.PRIVATE
        ):
            new_emails = []
            old_read_accessible_by = app.read_accessible_by or []
            old_write_accessible_by = app.write_accessible_by or []
            if "read_accessible_by" in request.data:
                # Filter out invalid email addresses from read_accessible_by
                valid_emails = []
                for email in request.data["read_accessible_by"]:
                    try:
                        validate_email(email)
                        valid_emails.append(email)
                    except ValidationError:
                        pass

                app.read_accessible_by = valid_emails[:20]

            if "write_accessible_by" in request.data:
                # Filter out invalid email addresses from write_accessible_by
                valid_emails = []
                for email in request.data["write_accessible_by"]:
                    try:
                        validate_email(email)
                        valid_emails.append(email)
                    except ValidationError:
                        pass

                app.write_accessible_by = valid_emails[:20]

            new_emails = list(
                set(app.read_accessible_by).union(set(app.write_accessible_by))
                - set(old_read_accessible_by).union(
                    set(old_write_accessible_by),
                ),
            )

            # Send email to new users
            # TODO: Use multisend to send emails in bulk
            for new_email in new_emails:
                email_template_cls = EmailTemplateFactory.get_template_by_name(
                    "app_shared",
                )
                share_email = email_template_cls(
                    uuid=app.uuid,
                    published_uuid=app.published_uuid,
                    app_name=app.name,
                    owner_first_name=app.owner.first_name,
                    owner_email=app.owner.email,
                    can_edit=app.has_write_permission(request.user),
                    share_to=new_email,
                )
                share_email_sender = EmailSender(share_email)
                share_email_sender.send()

        app_newly_published = not app.is_published
        app.is_published = True
        app.save()

        # Send app published email if the app was not published before
        if app_newly_published:
            email_template_cls = EmailTemplateFactory.get_template_by_name(
                "app_published",
            )
            app_published_email = email_template_cls(
                app_name=app.name,
                owner_first_name=app.owner.first_name,
                owner_email=app.owner.email,
                published_uuid=app.published_uuid,
            )
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
            return DRFResponse(
                status=500,
                errors={
                    "message": "Cannot delete a published app.",
                },
            )

        if app.owner != request.user:
            return DRFResponse(status=404)

        app.delete()

        # Delete AppData
        AppData.objects.filter(app_uuid=app.uuid).delete()

        return DRFResponse(status=200)

    def patch(self, request, uid):
        app = get_object_or_404(App, uuid=uuid.UUID(uid))
        app_owner_profile = get_object_or_404(Profile, user=app.owner)
        if not app.has_write_permission(request.user):
            return DRFResponse(status=403)

        app.name = request.data["name"] if "name" in request.data else app.name
        app.web_integration_config = (
            WebIntegrationConfig(**request.data["web_config"]).to_dict(
                app_owner_profile.encrypt_value,
            )
            if "web_config" in request.data and request.data["web_config"]
            else app.web_integration_config
        )
        app.slack_integration_config = (
            SlackIntegrationConfig(**request.data["slack_config"]).to_dict(
                app_owner_profile.encrypt_value,
            )
            if "slack_config" in request.data and request.data["slack_config"]
            else app.slack_integration_config
        )
        app.discord_integration_config = (
            DiscordIntegrationConfig(**request.data["discord_config"]).to_dict(
                app_owner_profile.encrypt_value,
            )
            if "discord_config" in request.data and request.data["discord_config"]
            else app.discord_integration_config
        )
        app.twilio_integration_config = (
            TwilioIntegrationConfig(**request.data["twilio_config"]).to_dict(
                app_owner_profile.encrypt_value,
            )
            if "twilio_config" in request.data and request.data["twilio_config"]
            else app.twilio_integration_config
        )
        draft = request.data["draft"] if "draft" in request.data else True
        comment = request.data["comment"] if "comment" in request.data else ""

        versioned_app_data = (
            AppData.objects.filter(
                app_uuid=app.uuid,
                is_draft=True,
            ).first()
            or AppData.objects.filter(
                app_uuid=app.uuid,
                is_draft=False,
            )
            .order_by("-created_at")
            .first()
        )

        processors_data = request.data["processors"] if "processors" in request.data else []
        processed_processors_data = (
            []
            if len(
                processors_data,
            )
            > 0
            else versioned_app_data.data["processors"]
        )
        try:
            for processor in processors_data:
                processor_cls = ProcessorFactory.get_api_processor(
                    processor["processor_slug"], processor["provider_slug"]
                )
                configuration_cls = processor_cls.get_configuration_cls()
                config_dict = configuration_cls(**processor["config"]).model_dump()
                processed_processors_data.append(
                    {**processor, **{"config": config_dict}},
                )
        except Exception:
            processed_processors_data = processors_data

        app_data_config = (
            request.data["config"]
            if "config" in request.data and request.data["config"]
            else (versioned_app_data.data["config"] if versioned_app_data else None)
        )
        if app_data_config:
            if "assistant_image" in app_data_config and app_data_config["assistant_image"]:
                if not app_data_config["assistant_image"].startswith("data:image"):
                    # This is a URL instead of objref
                    last_assistant_image = (
                        versioned_app_data.data["config"]["assistant_image"] if versioned_app_data else ""
                    )
                    if last_assistant_image and last_assistant_image.startswith("objref:"):
                        app_data_config["assistant_image"] = last_assistant_image

        # Find the versioned app data and update it
        app_data = {
            "name": request.data["name"] if "name" in request.data else versioned_app_data.data["name"],
            "description": (
                request.data["description"] if "description" in request.data else versioned_app_data.data["description"]
            ),
            "icon": (
                request.data["icon"]
                if "icon" in request.data
                else (
                    versioned_app_data.data.get("icon", None)
                    if versioned_app_data and versioned_app_data.data
                    else None
                )
            ),
            "type_slug": (
                request.data["type_slug"] if "type_slug" in request.data else versioned_app_data.data["type_slug"]
            ),
            "config": (
                request.data["config"]
                if "config" in request.data and request.data["config"]
                else versioned_app_data.data["config"]
            ),
            "input_fields": (
                request.data["input_fields"]
                if "input_fields" in request.data
                else versioned_app_data.data["input_fields"]
            ),
            "output_template": (
                request.data["output_template"]
                if "output_template" in request.data
                else versioned_app_data.data["output_template"]
            ),
            "processors": processed_processors_data,
        }

        if versioned_app_data:
            versioned_app_data.comment = comment
            versioned_app_data.data = app_data
            versioned_app_data.is_draft = draft
            versioned_app_data.save()
        else:
            # Find the total number of published versions
            published_versions = AppData.objects.filter(
                app_uuid=app.uuid,
                is_draft=False,
            ).count()
            AppData.objects.create(
                app_uuid=app.uuid,
                data=app_data,
                comment=comment,
                is_draft=draft,
                version=published_versions,
            )

        app.last_modified_by = request.user
        app.save()

        return DRFResponse(
            AppSerializer(
                instance=app,
                request_user=request.user,
            ).data,
            status=201,
        )

    def post(self, request):
        owner = request.user
        app_owner_profile = get_object_or_404(Profile, user=owner)
        app_type_slug = request.data["type_slug"] if "type_slug" in request.data else None
        app_type = (
            get_object_or_404(
                AppType,
                id=request.data["app_type"],
            )
            if "app_type" in request.data
            else get_object_or_404(
                AppType,
                slug=app_type_slug,
            )
        )
        app_name = request.data["name"]
        app_description = request.data["description"] if "description" in request.data else ""
        app_icon = request.data["icon"] if "icon" in request.data else None
        app_config = request.data["config"] if "config" in request.data else {}
        app_input_fields = request.data["input_fields"] if "input_fields" in request.data else []
        app_output_template = request.data["output_template"] if "output_template" in request.data else {}
        app_processors = request.data["processors"] if "processors" in request.data else []
        web_integration_config = (
            WebIntegrationConfig(
                **request.data["web_config"],
            ).to_dict(
                app_owner_profile.encrypt_value,
            )
            if "web_config" in request.data and request.data["web_config"]
            else {}
        )
        slack_integration_config = (
            SlackIntegrationConfig(
                **request.data["slack_config"],
            ).to_dict(
                app_owner_profile.encrypt_value,
            )
            if "slack_config" in request.data and request.data["slack_config"]
            else {}
        )
        discord_integration_config = (
            DiscordIntegrationConfig(
                **request.data["discord_config"],
            ).to_dict(
                app_owner_profile.encrypt_value,
            )
            if "discord_config" in request.data and request.data["discord_config"]
            else {}
        )
        twilio_integration_config = (
            TwilioIntegrationConfig(
                **request.data["twilio_config"],
            ).to_dict(
                app_owner_profile.encrypt_value,
            )
            if "twilio_config" in request.data and request.data["twilio_config"]
            else {}
        )
        draft = request.data["draft"] if "draft" in request.data else True
        is_published = request.data["is_published"] if "is_published" in request.data else False
        comment = request.data["comment"] if "comment" in request.data else "First version"

        template_slug = request.data["template_slug"] if "template_slug" in request.data else None

        app = App.objects.create(
            name=app_name,
            owner=owner,
            description=app_description,
            type=app_type,
            template_slug=template_slug,
            web_integration_config=web_integration_config,
            slack_integration_config=slack_integration_config,
            discord_integration_config=discord_integration_config,
            twilio_integration_config=twilio_integration_config,
        )
        app_data = {
            "name": app_name,
            "description": app_description,
            "type_slug": app_type.slug,
            "description": app_description,
            "config": app_config,
            "input_fields": app_input_fields,
            "output_template": app_output_template,
            "processors": app_processors,
        }

        # Add app icon to app data if it exists
        if app_icon:
            app_data["icon"] = app_icon

        AppData.objects.create(
            app_uuid=app.uuid,
            data=app_data,
            is_draft=draft,
            comment=comment,
        )

        if is_published and not draft:
            self.publish(request, str(app.uuid))

        return DRFResponse(AppSerializer(instance=app).data, status=201)

    @action(detail=True, methods=["post"])
    @xframe_options_exempt
    def run(self, request, app_uuid, session_id=None, platform=None):
        stream = request.data.get("stream", False)
        request_uuid = str(uuid.uuid4())
        try:
            result = self.run_app_internal(
                app_uuid,
                session_id,
                request_uuid,
                request,
                platform,
            )
            if stream:
                response = StreamingHttpResponse(
                    streaming_content=result,
                    content_type="application/json",
                )
                response.is_async = True
                return response
            response_body = {k: v for k, v in result.items() if k != "csp"}
            response_body["_id"] = request_uuid
            return DRFResponse(
                response_body,
                status=200,
                headers={
                    "Content-Security-Policy": result["csp"] if "csp" in result else "frame-ancestors self",
                },
            )
        except AppRunnerException as e:
            logger.exception("Error while running app")
            return DRFResponse({"errors": [str(e)]}, status=e.status_code)
        except Exception as e:
            logger.exception("Error while running app")
            return DRFResponse({"errors": [str(e)]}, status=400)

    async def init_app_async(self, uid):
        return await database_sync_to_async(self.init_app)(uid)

    def init_app(self, uid):
        session_id = str(uuid.uuid4())

        create_app_session(session_id)

        return session_id

    def processor_run(self, request, uid, id):
        stream = False
        request_uuid = str(uuid.uuid4())
        preview = request.data.get("preview", False)
        session_id = request.data.get("session_id", None)
        disable_history = request.data.get("disable_history", False)

        try:
            result = self.run_processor_internal(
                uid,
                id,
                session_id,
                request_uuid,
                request,
                None,
                preview,
                disable_history,
            )
            if stream:
                response = StreamingHttpResponse(
                    streaming_content=result,
                    content_type="application/json",
                )
                response.is_async = True
                return response
            response_body = {k: v for k, v in result.items() if k != "csp"}
            response_body["_id"] = request_uuid
            return DRFResponse(
                response_body,
                status=200,
                headers={
                    "Content-Security-Policy": result["csp"] if "csp" in result else "frame-ancestors self",
                },
            )
        except AppRunnerException as e:
            logger.exception("Error while running app")
            return DRFResponse({"errors": [str(e)]}, status=e.status_code)
        except Exception as e:
            logger.exception("Error while running app")
            return DRFResponse({"errors": [str(e)]}, status=400)

    async def run_app_internal_async(self, uid, session_id, request_uuid, request, preview=False):
        return await database_sync_to_async(self.run_app_internal)(
            uid,
            session_id,
            request_uuid,
            request,
            preview=preview,
        )

    async def run_playground_internal_async(self, session_id, request_uuid, request, preview=False):
        return await database_sync_to_async(self.run_playground_internal)(
            session_id,
            request_uuid,
            request,
            platform="playground",
            preview=False,
            disable_history=False,
        )

    def run_playground_internal(
        self,
        session_id,
        request_uuid,
        request,
        platform="playground",
        preview=False,
        disable_history=False,
    ):
        request_ip = request.headers.get("X-Forwarded-For", request.META.get("REMOTE_ADDR", "")).split(",")[
            0
        ].strip() or request.META.get("HTTP_X_REAL_IP", "")

        request_location = request.headers.get("X-Client-Geo-Location", "")

        if not request_location:
            location = get_location(request_ip)
            request_location = f"{location.get('city', '')}, {location.get('country_code', '')}" if location else ""

        if flag_enabled(
            "HAS_EXCEEDED_MONTHLY_PROCESSOR_RUN_QUOTA",
            request=request,
            user=request.user,
        ):
            raise Exception(
                "You have exceeded your monthly processor run quota. Please upgrade your plan to continue using the platform.",
            )

        processor_id = request.data["input"]["api_provider_slug"] + "_" + request.data["input"]["api_backend_slug"]

        app_runner = None

        return app_runner.run_app(processor_id=processor_id)

    async def run_platform_app_internal_async(self, session_id, request_uuid, request, preview=False):
        return await database_sync_to_async(self.run_platform_app_internal)(
            session_id,
            request_uuid,
            request,
            platform="platform-app",
            preview=False,
            disable_history=False,
        )

    def run_platform_app_internal(
        self, session_id, request_uuid, request, platform="platform-app", preview=False, disable_history=False
    ):
        from llmstack.apps.handlers.platform_app_runner import (
            PlatformApp,
            PlatformAppRunner,
            PlatformAppType,
        )

        stream = request.data.get("stream", False)
        request_ip = request.headers.get("X-Forwarded-For", request.META.get("REMOTE_ADDR", "")).split(",")[
            0
        ].strip() or request.META.get("HTTP_X_REAL_IP", "")

        request_location = request.headers.get("X-Client-Geo-Location", "")
        if not request_location:
            location = get_location(request_ip)
            request_location = f"{location.get('city', '')}, {location.get('country_code', '')}" if location else ""

        request_user_agent = request.META.get("HTTP_USER_AGENT", "")
        request_content_type = request.META.get("CONTENT_TYPE", "")

        if flag_enabled(
            "HAS_EXCEEDED_MONTHLY_PROCESSOR_RUN_QUOTA",
            request=request,
            user=request.user,
        ):
            raise Exception(
                "You have exceeded your monthly processor run quota. Please upgrade your plan to continue using the platform.",
            )

        app_owner_profile = (
            Profile.objects.get(user=request.user) if request.user.is_authenticated else AnonymousProfile()
        )

        owner_connections = get_connections(app_owner_profile) if request.user.is_authenticated else {}
        app_data = request.data["app_data"]
        app_slug = app_data.get("slug", "platform-app")
        app_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, app_slug)
        app = PlatformApp(
            id="",
            uuid=str(app_uuid),
            type=PlatformAppType(slug=str(app_data["type_slug"])),
            web_integration_config={},
            is_published=True,
        )
        processors = app_data["processors"]
        output_template = app_data["output_template"]
        app_data_config = app_data["config"]

        app_runner = PlatformAppRunner(
            app=app,
            app_data={
                "config": app_data_config,
                "processors": processors,
                "output_template": output_template,
                "type_slug": app_data["type_slug"],
            },
            request_uuid=request_uuid,
            request=request,
            session_id=session_id,
            app_owner=app_owner_profile,
            stream=stream,
            request_ip=request_ip,
            request_location=request_location,
            request_user_agent=request_user_agent,
            request_content_type=request_content_type,
            connections=owner_connections,
        )

        return app_runner.run_app()

    async def get_app_runner_async(
        self,
        session_id,
        app_uuid,
        source,
        request_user,
        preview=False,
        app_data=None,
    ):
        runner_user = request_user
        if not app_data:
            app = await aget_object_or_404(App, uuid=uuid.UUID(app_uuid))
            app_data_obj = (
                await AppData.objects.filter(
                    app_uuid=app.uuid,
                    is_draft=preview,
                )
                .order_by("-created_at")
                .afirst()
            )
            if not app_data_obj:
                raise Exception("App data not found")
            app_data = app_data_obj.data

            if not runner_user:
                runner_user = app.owner

        app_run_user_profile = await Profile.objects.aget(user=runner_user)
        vendor_env = {
            "provider_configs": await database_sync_to_async(app_run_user_profile.get_merged_provider_configs)(),
        }

        return AppRunner(
            session_id=session_id,
            app_data=app_data,
            source=source,
            vendor_env=vendor_env,
        )

    def get_app_runner(self, session_id, app_uuid, source, request_user, preview=False, app_data=None):
        return async_to_sync(self.get_app_runner_async)(
            session_id,
            app_uuid,
            source,
            request_user,
            preview,
            app_data,
        )

    def run_app_internal(
        self,
        app_uuid,
        session_id,
        request_uuid,
        request,
        platform=None,
        preview=False,
        version=None,
        app_store_uuid=None,
        app_store_app_data=None,
    ):
        app = (
            get_object_or_404(App, uuid=uuid.UUID(app_uuid))
            if not app_store_app_data
            else App(
                name=app_store_app_data.get("name", ""),
                store_uuid=app_store_uuid,
                uuid=app_uuid if app_uuid else app_store_uuid,
                owner=request.user,
                type=AppType(slug=app_store_app_data.get("type_slug", "agent")),
                is_published=True,
            )
        )
        app_owner = get_object_or_404(Profile, user=app.owner)
        owner_connections = get_connections(app_owner)
        stream = request.data.get("stream", False)
        request_ip = request.headers.get(
            "X-Forwarded-For",
            request.META.get(
                "REMOTE_ADDR",
                "",
            ),
        ).split(
            ",",
        )[0].strip() or request.META.get(
            "HTTP_X_REAL_IP",
            "",
        )
        request_location = request.headers.get("X-Client-Geo-Location", "")
        if not request_location:
            location = get_location(request_ip)
            request_location = f"{location.get('city', '')}, {location.get('country_code', '')}" if location else ""

        request_user_agent = request.META.get("HTTP_USER_AGENT", "")
        request_content_type = request.META.get("CONTENT_TYPE", "")

        if flag_enabled(
            "HAS_EXCEEDED_MONTHLY_PROCESSOR_RUN_QUOTA",
            request=request,
            user=app.owner,
        ):
            raise Exception(
                "You have exceeded your monthly processor run quota. Please upgrade your plan to continue using the platform.",
            )

        app_data_obj = (
            (
                AppData.objects.filter(
                    app_uuid=app.uuid,
                    is_draft=preview,
                )
                .order_by("-created_at")
                .first()
                if version is None
                else AppData.objects.filter(
                    app_uuid=app.uuid,
                    version=version,
                    is_draft=False,
                ).first()
            )
            if not app_store_app_data
            else AppData(
                app_uuid=app.uuid,
                data=app_store_app_data,
                is_draft=False,
            )
        )

        # If we are running a published app, use the published app data
        if not app_data_obj and preview:
            app_data_obj = (
                AppData.objects.filter(
                    app_uuid=app.uuid,
                    is_draft=False,
                )
                .order_by("-created_at")
                .first()
            )

        app_runner_class = None

        app_runner = app_runner_class(
            app=app,
            app_data=app_data_obj.data if app_data_obj else None,
            request_uuid=request_uuid,
            request=request,
            session_id=session_id,
            app_owner=app_owner,
            stream=stream,
            request_ip=request_ip,
            request_location=request_location,
            request_user_agent=request_user_agent,
            request_content_type=request_content_type,
            app_store_uuid=app_store_uuid,
            connections=owner_connections,
        )

        return app_runner.run_app()

    def run_processor_internal(
        self,
        uid,
        processor_id,
        session_id,
        request_uuid,
        request,
        platform=None,
        preview=False,
        disable_history=False,
    ):
        app = get_object_or_404(App, uuid=uuid.UUID(uid))

        request_ip = request.headers.get(
            "X-Forwarded-For",
            request.META.get(
                "REMOTE_ADDR",
                "",
            ),
        ).split(
            ",",
        )[0].strip() or request.META.get(
            "HTTP_X_REAL_IP",
            "",
        )

        request_location = request.headers.get("X-Client-Geo-Location", "")

        if not request_location:
            location = get_location(request_ip)
            request_location = f"{location.get('city', '')}, {location.get('country_code', '')}" if location else ""

        if flag_enabled(
            "HAS_EXCEEDED_MONTHLY_PROCESSOR_RUN_QUOTA",
            request=request,
            user=app.owner,
        ):
            raise Exception(
                "You have exceeded your monthly processor run quota. Please upgrade your plan to continue using the platform.",
            )

        app_data_obj = (
            AppData.objects.filter(
                app_uuid=app.uuid,
                is_draft=preview,
            )
            .order_by("-created_at")
            .first()
        )

        # If we are running a published app, use the published app data
        if not app_data_obj and preview:
            app_data_obj = (
                AppData.objects.filter(
                    app_uuid=app.uuid,
                    is_draft=False,
                )
                .order_by("-created_at")
                .first()
            )

        app_runner = None

        return app_runner.run_app(processor_id=processor_id)

    @action(detail=True, methods=["post"])
    def run_discord(self, request, uid):
        # If the request is a url verification request, return the challenge
        if request.data.get("type") == 1:
            return DRFResponse(status=200, data={"type": 1})

        return self.run(request, uid, platform="discord")

    @action(detail=True, methods=["post"])
    def run_slack(self, request, uid):
        # If the request is a url verification request, return the challenge
        if request.data.get("type") == "url_verification":
            return DRFResponse(
                status=200,
                data={
                    "challenge": request.data["challenge"],
                },
            )

        return self.run(request, uid, platform="slack")

    @action(detail=True, methods=["post"])
    def run_twiliosms(self, request, uid):
        self.run(request, uid, platform="twilio-sms")
        return DRFResponse(status=204, headers={"Content-Type": "text/xml"})

    @action(detail=True, methods=["post"])
    def run_twiliovoice(self, request, uid):
        raise NotImplementedError()


class AppHubViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    # @method_decorator(cache_page(60*60*24))
    def list(self, request):
        apphub_objs = AppHub.objects.all().order_by("rank")

        return DRFResponse(
            AppHubSerializer(
                instance=apphub_objs,
                many=True,
            ).data,
        )


class PlatformAppsViewSet(viewsets.ViewSet):
    def list(self, request):
        result = []
        if settings.PLATFORM_APPS_DIR:
            apps_dir = settings.PLATFORM_APPS_DIR
            for entry in apps_dir:
                yml_files = [
                    f for f in os.listdir(entry) if os.path.isfile(os.path.join(entry, f)) and f.endswith(".yml")
                ]
                for yml_file in yml_files:
                    with open(os.path.join(entry, yml_file), "r") as stream:
                        app_data = yaml.safe_load(stream)
                        result.append(app_data)
        return DRFResponse(result)

    def get(self, request, slug):
        apps = self.list(request)
        for app in apps.data:
            if app["slug"] == slug:
                return DRFResponse(app)

        return DRFResponse(status=404)

    def run(self, request, slug):
        app_data = self.get(request, slug).data
        app_data = {**app_data, **request.data.get("app_data", {})}

        request.data["app_data"] = app_data
        response = AppViewSet().run_platform_app_internal(
            session_id=None, request_uuid=str(uuid.uuid4()), request=request
        )

        return DRFResponse(data=response, status=200)

    def run_with_app_data(self, request):
        app_data = request.data.get("app_data", {})
        app_data["slug"] = "platform-app"
        request.data["app_data"] = app_data
        response = AppViewSet().run_platform_app_internal(
            session_id=None, request_uuid=str(uuid.uuid4()), request=request
        )

        return DRFResponse(data=response, status=200)


class PlaygroundViewSet(viewsets.ViewSet):
    async def get_app_runner_async(self, session_id, source, request_user, input_data, config_data):
        runner_user = request_user
        processor_slug = source.processor_slug
        provider_slug = source.provider_slug
        app_run_user_profile = await Profile.objects.aget(user=runner_user)

        vendor_env = {
            "provider_configs": await database_sync_to_async(app_run_user_profile.get_merged_provider_configs)(),
        }

        processor_cls = ProcessorFactory.get_processor(processor_slug=processor_slug, provider_slug=provider_slug)
        input_schema = json.loads(processor_cls.get_input_schema())
        input_fields = []
        for property in input_schema["properties"]:
            input_fields.append({"name": property, "type": input_schema["properties"][property]["type"]})

        app_data = {
            "name": f"Processor {provider_slug}_{processor_slug}",
            "config": {},
            "type_slug": "",
            "processors": [
                {
                    "id": "processor",
                    "name": processor_cls.name(),
                    "input": input_data,
                    "config": config_data,
                    "description": processor_cls.description(),
                    "dependencies": ["input"],
                    "provider_slug": provider_slug,
                    "processor_slug": processor_slug,
                    "output_template": processor_cls.get_output_template().model_dump(),
                }
            ],
            "description": "",
            "input_fields": input_fields,
            "output_template": {"markdown": "{{processor}}"},
        }
        return AppRunner(
            session_id=session_id,
            app_data=app_data,
            source=source,
            vendor_env=vendor_env,
        )

    def get_app_runner(self, session_id, source, request_user, input_data, config_data):
        return async_to_sync(self.get_app_runner_async)(session_id, source, request_user, input_data, config_data)
