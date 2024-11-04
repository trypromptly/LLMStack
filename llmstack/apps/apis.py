import asyncio
import hashlib
import hmac
import json
import logging
import re
import uuid
from time import time

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser, User
from django.core.validators import validate_email
from django.db.models import Q
from django.forms import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.test import RequestFactory
from django.views.decorators.clickjacking import xframe_options_exempt
from drf_yaml.parsers import YAMLParser
from flags.state import flag_enabled
from rest_framework import viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response as DRFResponse

from llmstack.apps.integration_configs import (
    DiscordIntegrationConfig,
    SlackIntegrationConfig,
    TwilioIntegrationConfig,
    WebIntegrationConfig,
)
from llmstack.apps.runner.app_runner import (
    APIAppRunnerSource,
    AppRunner,
    AppRunnerRequest,
    DiscordAppRunnerSource,
    SlackAppRunnerSource,
    TwilioAppRunnerSource,
    WebAppRunnerSource,
)
from llmstack.apps.yaml_loader import (
    get_app_template_by_slug,
    get_app_templates_from_contrib,
)
from llmstack.base.models import Profile
from llmstack.common.utils import prequests
from llmstack.emails.sender import EmailSender
from llmstack.emails.templates.factory import EmailTemplateFactory
from llmstack.jobs.adhoc import ProcessingJob
from llmstack.processors.providers.processors import ProcessorFactory

from .models import App, AppData, AppSessionFiles, AppType, AppVisibility
from .serializers import AppDataSerializer, AppSerializer

logger = logging.getLogger(__name__)


def upload_file_fn(file, session_id, app_uuid, user):
    if not file:
        return None

    file_obj = AppSessionFiles.create_from_data_uri(
        file, ref_id=session_id, metadata={"username": user, "app_uuid": app_uuid}
    )

    return f"objref://sessionfiles/{file_obj.uuid}" if file_obj else None


class AppViewSet(viewsets.ViewSet):
    parser_classes = (JSONParser, FormParser, MultiPartParser, YAMLParser)

    def get_permissions(self):
        if self.action == "getByPublishedUUID" or self.action == "run":
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

        if versioned_app_data and (
            (versioned_app_data.is_draft and draft) or (versioned_app_data.is_draft and not draft)
        ):
            # Update existing draft version
            versioned_app_data.comment = comment
            versioned_app_data.data = app_data
            versioned_app_data.is_draft = draft
            versioned_app_data.save()
        elif versioned_app_data and not versioned_app_data.is_draft and draft:
            # Create new draft version from published version
            published_versions = AppData.objects.filter(
                app_uuid=app.uuid,
                is_draft=False,
            ).count()

            AppData.objects.create(
                app_uuid=app.uuid,
                data=app_data,
                comment=comment,
                is_draft=True,
                version=published_versions,
            )
        else:
            # Create new version (either draft or published)
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
            AppType.objects.filter(id=request.data["app_type"]).first()
            if "app_type" in request.data
            else AppType.objects.filter(slug=app_type_slug).first()
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
            type_slug=app_type.slug if app_type else app_type_slug,
            template_slug=template_slug,
            web_integration_config=web_integration_config,
            slack_integration_config=slack_integration_config,
            discord_integration_config=discord_integration_config,
            twilio_integration_config=twilio_integration_config,
        )
        app_data = {
            "name": app_name,
            "description": app_description,
            "type_slug": app_type.slug if app_type else app_type_slug,
            "description": app_description,
            "config": app_config,
            "input_fields": app_input_fields,
            "output_template": app_output_template,
            "processors": app_processors,
        }

        if app_type_slug == "voice-agent":
            app_data["input_fields"] = [
                {
                    "name": "task",
                    "type": "multi",
                    "stream": True,
                    "required": True,
                    "description": "What do you want the agent to perform?",
                    "placeholder": "Type in your message",
                },
            ]

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

    async def get_app_runner_async(
        self,
        session_id,
        app_uuid,
        source,
        request_user,
        preview=False,
        app_data_config_override={},
    ):
        runner_user = request_user
        app = await App.objects.select_related("owner").aget(uuid=uuid.UUID(app_uuid))
        app_data_obj = (
            await AppData.objects.filter(
                app_uuid=app.uuid,
                is_draft=preview,
            )
            .order_by("-created_at")
            .afirst()
        )
        if not app_data_obj and preview:
            app_data_obj = await AppData.objects.filter(app_uuid=app.uuid).order_by("-created_at").afirst()

        if not app_data_obj:
            raise Exception("App data not found")
        app_data = app_data_obj.data

        if app_data_config_override:
            app_data["config"] = {**app_data["config"], **app_data_config_override}

        # We will always use app owner credentials for running the app
        credentials_user = app.owner

        if runner_user is None or runner_user.is_anonymous:
            runner_user = app.owner

        credentials_user_profile = await Profile.objects.aget(user=credentials_user)
        vendor_env = {
            "provider_configs": await database_sync_to_async(credentials_user_profile.get_merged_provider_configs)(),
            "connections": credentials_user_profile.connections,
        }

        return AppRunner(
            session_id=session_id,
            app_data=app_data,
            source=source,
            vendor_env=vendor_env,
            file_uploader=upload_file_fn,
        )

    def get_app_runner(self, session_id, app_uuid, source, request_user, preview=False, app_data=None):
        return async_to_sync(self.get_app_runner_async)(session_id, app_uuid, source, request_user, preview)

    def _run_internal(self, request, app_uuid, input_data, source, app_data, session_id, stream):
        app_runner = AppViewSet().get_app_runner(
            session_id=session_id,
            app_uuid=app_uuid,
            source=source,
            request_user=request.user if request.user.is_authenticated else None,
            preview=False,
            app_data=app_data,
        )
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = app_runner.run_until_complete(
            AppRunnerRequest(client_request_id=str(uuid.uuid4()), session_id=session_id, input=input_data), loop
        )
        return response

    def run(self, request, uid):
        if request.user.is_anonymous:
            return DRFResponse(status=403)
        app = get_object_or_404(App, uuid=uuid.UUID(uid))

        if not app.has_read_permission(request.user):
            return DRFResponse(status=403)

        app_data_obj = AppData.objects.filter(app_uuid=app.uuid).order_by("-created_at").first()
        if not app_data_obj:
            return DRFResponse(status=404)

        csp = "frame-ancestors self"
        if app.is_published:
            if app.visibility == AppVisibility.PUBLIC:
                csp = "frame-ancestors *"
            if app.web_config:
                if app.web_config.get("allowed_sites", []):
                    csp = "frame-ancestors " + " ".join(app.web_config["allowed_sites"])

        session_id = request.data.get("session_id", str(uuid.uuid4()))
        input_data = request.data.get("input", {})

        request_ip = request.headers.get("X-Forwarded-For", request.META.get("REMOTE_ADDR", "")).split(",")[
            0
        ].strip() or request.META.get("HTTP_X_REAL_IP", "")

        request_location = request.headers.get("X-Client-Geo-Location", "")

        app_run_response = self._run_internal(
            request,
            uid,
            input_data,
            APIAppRunnerSource(
                request_ip=request_ip,
                request_location=request_location,
                request_user_agent=request.headers.get("User-Agent", ""),
                request_content_type=request.headers.get("Content-Type", ""),
                app_uuid=uid,
                request_user_email=request.user.email,
            ),
            app_data_obj.data,
            session_id,
            False,
        )
        response = app_run_response.data.model_dump()
        response["session"] = {"id": session_id}
        return DRFResponse(data=response, status=200, headers={"Content-Security-Policy": csp})


class PlaygroundViewSet(viewsets.ViewSet):
    async def get_app_runner_async(self, session_id, source, request_user, input_data, config_data):
        runner_user = request_user
        processor_slug = source.processor_slug
        provider_slug = source.provider_slug
        app_run_user_profile = await Profile.objects.aget(user=runner_user)

        vendor_env = {
            "provider_configs": await database_sync_to_async(app_run_user_profile.get_merged_provider_configs)(),
            "connections": app_run_user_profile.connections,
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
            "spread_output_for_keys": ["processor"],
            "processors": [
                {
                    "id": "processor",
                    "name": processor_cls.name(),
                    "input": input_data,
                    "config": config_data,
                    "description": processor_cls.description(),
                    "dependencies": ["_inputs0"],
                    "provider_slug": provider_slug,
                    "processor_slug": processor_slug,
                    "output_template": processor_cls.get_output_template().model_dump(),
                }
            ],
            "description": "",
            "input_fields": input_fields,
            "output_template": processor_cls.get_output_template().model_dump(),
        }
        return AppRunner(
            session_id=session_id,
            app_data=app_data,
            source=source,
            vendor_env=vendor_env,
        )

    def get_app_runner(self, session_id, source, request_user, input_data, config_data):
        return async_to_sync(self.get_app_runner_async)(session_id, source, request_user, input_data, config_data)


class APIViewSet(viewsets.ViewSet):
    @staticmethod
    def run_internal(request, app_uuid, input_data, source, app_data, session_id, stream=False):
        app_runner = AppViewSet().get_app_runner(
            session_id=session_id,
            app_uuid=app_uuid,
            source=source,
            request_user=request.user if request.user.is_authenticated else None,
            preview=False,
            app_data=app_data,
        )
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        app_run_response = app_runner.run_until_complete(
            AppRunnerRequest(client_request_id=str(uuid.uuid4()), session_id=session_id, input=input_data), loop
        )
        return DRFResponse(data=app_run_response.data.model_dump(), status=200)

    def run(self, request, uid):
        if request.user.is_anonymous:
            return DRFResponse(status=403)

        app = get_object_or_404(App, uuid=uuid.UUID(uid))
        if app.owner != request.user:
            return DRFResponse(status=403)

        preview = request.data.get("preview", False)
        app_data_obj = AppData.objects.filter(app_uuid=app.uuid, is_draft=preview).order_by("-created_at").first()
        if not app_data_obj:
            return DRFResponse(status=404)

        session_id = request.data.get("session_id", str(uuid.uuid4()))
        stream = request.data.get("stream", False)
        input_data = request.data.get("input", {})
        request_ip = request.headers.get("X-Forwarded-For", request.META.get("REMOTE_ADDR", "")).split(",")[
            0
        ].strip() or request.META.get("HTTP_X_REAL_IP", "")

        request_location = request.headers.get("X-Client-Geo-Location", "")

        return self.run_internal(
            request,
            uid,
            input_data,
            WebAppRunnerSource(
                request_ip=request_ip,
                request_location=request_location,
                request_user_agent=request.headers.get("User-Agent", ""),
                request_content_type=request.headers.get("Content-Type", ""),
                app_uuid=uid,
                request_user_email=request.user.email,
            ),
            app_data_obj.data,
            session_id,
            stream,
        )


class RunAppAsyncJob(ProcessingJob):
    @classmethod
    def generate_job_id(cls):
        return "{}".format(str(uuid.uuid4()))


def run_discord_app(request, uid, input_data, source, app_data, session_id, stream=False):
    DiscordViewSet()._run(request, uid, input_data, source, app_data, session_id, stream)


class DiscordViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def _run(self, request, uid, input_data, source, app_data, session_id, stream=False):
        app = get_object_or_404(App, uuid=uuid.UUID(uid))
        if app.discord_config:
            response = APIViewSet().run_internal(
                request=request,
                app_uuid=uid,
                input_data=input_data,
                source=source,
                app_data=app_data,
                session_id=session_id,
                stream=stream,
            )
            response_text = (
                response.data.get("output", {}).get("output")
                or (" ".join(response.data.get("output", {}).get("errors", [])) or "An error occurred.")
                if response.status_code == 200
                else "An error occurred."
            )
            token = input_data.get("_request", {}).get("token")
            app_id = app.discord_config.get("app_id")

            prequests.post(
                url=f"https://discord.com/api/v10/webhooks/{app_id}/{token}",
                headers={
                    "Authorization": f"Bot {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "content": response_text,
                },
            )

    def run_async(self, request, uid):
        if request.data.get("type") == 1:
            return DRFResponse(status=200, data={"type": 1})

        if request.data.get("type") == 2:
            app = get_object_or_404(App, uuid=uuid.UUID(uid))
            if app.visibility == AppVisibility.PUBLIC:
                app_data_obj = AppData.objects.filter(app_uuid=app.uuid, is_draft=False).order_by("-created_at").first()
                if app_data_obj:
                    if app.discord_config and request.data["data"]["name"] == app.discord_config["slash_command_name"]:
                        session_id = str(uuid.uuid5(uuid.NAMESPACE_URL, request.data["id"]))
                        request_user = AnonymousUser()
                        discord_input = {}
                        for option in request.data["data"]["options"]:
                            discord_input[option["name"]] = option["value"]

                        input_data = {
                            **discord_input,
                            "_request": {
                                "user": request.data["member"]["user"]["id"],
                                "username": request.data["member"]["user"]["username"],
                                "global_name": request.data["member"]["user"]["global_name"],
                                "channel": request.data["channel_id"],
                                "guild_id": request.data["guild_id"],
                                "token": request.data["token"],
                            },
                        }
                        new_request = RequestFactory().post("/api/apps/{}/run".format(uid))
                        new_request.user = request_user
                        new_request.data = {"input": input_data, "session_id": session_id}
                        source = DiscordAppRunnerSource(request_user_email=None, app_uuid=uid)

                        RunAppAsyncJob.create(
                            func="llmstack.apps.apis.run_discord_app",
                            args=[new_request, uid, input_data, source, app_data_obj.data, session_id, False],
                        ).add_to_queue()

        return DRFResponse(status=200, data={"type": 5})


def run_slack_app(request, uid, input_data, source, app_data, session_id, stream=False):
    SlackViewSet._run(request, uid, input_data, source, app_data, session_id, stream)


class SlackViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @classmethod
    def verify_request_signature(
        cls,
        signing_secret: str,
        headers: dict,
        raw_body: bytes,
    ):
        signature = headers.get("X-Slack-Signature")
        timestamp = headers.get("X-Slack-Request-Timestamp")
        if signature and timestamp and raw_body:
            if signing_secret:
                if abs(time() - int(timestamp)) > 60 * 5:
                    return False
                format_req = str.encode(
                    f"v0:{timestamp}:{raw_body.decode('utf-8')}",
                )
                encoded_secret = str.encode(signing_secret)
                request_hash = hmac.new(
                    encoded_secret,
                    format_req,
                    hashlib.sha256,
                ).hexdigest()
                if f"v0={request_hash}" == signature:
                    return True
        return False

    def _get_slack_app_session_id(self, slack_request_event_data, app_uuid):
        thread_ts = slack_request_event_data.get("thread_ts") or slack_request_event_data.get("ts")
        identifier_prefix = slack_request_event_data.get("channel") or slack_request_event_data.get("user")
        session_identifier = f"{identifier_prefix}_{thread_ts}"
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{str(app_uuid)}-{session_identifier}"))

    def _get_request_user(self, slack_user_id, slack_bot_token):
        http_request = prequests.get(
            "https://slack.com/api/users.info",
            params={"user": slack_user_id},
            headers={"Authorization": f"Bearer {slack_bot_token}"},
        )

        slack_user = None
        if http_request.status_code == 200:
            http_response = http_request.json()
            slack_user = http_response["user"]["profile"]

        if slack_user and slack_user.get("email"):
            return User.objects.filter(email=slack_user["email"]).first()

        return AnonymousUser()

    @staticmethod
    def _run(request, uid, input_data, source, app_data, session_id, stream=False):
        app = App.objects.filter(uuid=uid).first()
        if app and app.slack_config:
            response = APIViewSet().run_internal(
                request=request,
                app_uuid=uid,
                input_data=input_data,
                source=source,
                session_id=session_id,
                stream=stream,
                app_data=app_data,
            )
            response_text = (
                response.data.get("output", {}).get("output")
                or (" ".join(response.data.get("output", {}).get("errors", [])) or "An error occurred.")
                if response.status_code == 200
                else "An error occurred."
            )
            response_channel = input_data.get("_request", {}).get("channel")
            response_thread_ts = input_data.get("_request", {}).get("thread_ts") or input_data.get("_request", {}).get(
                "ts"
            )
            token = app.slack_config.get("bot_token")

            prequests.post(
                "https://slack.com/api/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "channel": response_channel,
                    "thread_ts": response_thread_ts,
                    "text": response_text,
                    "blocks": [],
                },
                timeout=60,
            )

    def run_async(self, request, uid):
        if request.data.get("type") == "url_verification":
            return DRFResponse(
                status=200,
                data={
                    "challenge": request.data["challenge"],
                },
            )

        if request.headers.get("X-Slack-Request-Timestamp") is None or request.headers.get("X-Slack-Signature") is None:
            return DRFResponse(status=403, data={"error": "Invalid request"})

        slack_request_body = request.body
        request_type = request.data.get("type")

        if request_type == "event_callback":
            event_data = self.request.data.get("event", {})

            event_type = event_data.get("type")
            channel_type = event_data.get("channel_type")
            # Respond to app mentions and direct messages from users
            if (event_type == "app_mention") or (
                event_type == "message"
                and channel_type == "im"
                and "subtype" not in event_data
                and "bot_id" not in event_data
            ):
                app = get_object_or_404(App, uuid=uuid.UUID(uid))
                app_data_obj = AppData.objects.filter(app_uuid=app.uuid, is_draft=False).order_by("-created_at").first()

                if (
                    app_data_obj
                    and app.slack_config
                    and request.data.get("token") == app.slack_config.get("verification_token")
                    and request.data.get("api_app_id") == app.slack_config.get("app_id")
                    and SlackViewSet.verify_request_signature(
                        app.slack_config.get("signing_secret"), request.headers, slack_request_body
                    )
                ):
                    request_user = self._get_request_user(
                        request.data["event"]["user"], app.slack_config.get("bot_token")
                    )
                    # Improve this check later
                    if app.visibility == AppVisibility.PUBLIC or (
                        app.visibility < AppVisibility.PUBLIC and request_user and request_user.is_authenticated
                    ):
                        session_id = self._get_slack_app_session_id(request.data, uid)
                        slack_message_text = re.sub(r"<@.*>(\|)?", "", request.data["event"]["text"]).strip()
                        request_user_email = request_user.email if request_user else None
                        input_data = {
                            **dict(
                                zip(
                                    list(map(lambda x: x["name"], app_data_obj.data["input_fields"])),
                                    [slack_message_text] * len(app_data_obj.data["input_fields"]),
                                ),
                            ),
                            "_request": {
                                "text": event_data.get("text"),
                                "user": event_data.get("user"),
                                "slack_user_email": request_user_email,
                                "token": request.data["token"],
                                "team_id": request.data["team_id"],
                                "api_app_id": request.data["api_app_id"],
                                "team": event_data.get("team"),
                                "channel": event_data.get("channel"),
                                "text-type": event_data.get("type"),
                                "ts": event_data.get("ts"),
                                "thread_ts": event_data.get("thread_ts"),
                            },
                        }

                        new_request = RequestFactory().post("/api/apps/{}/run".format(uid))
                        new_request.user = request_user or AnonymousUser()
                        new_request.data = {"input": input_data, "session_id": session_id}

                        source = SlackAppRunnerSource(request_user_email=request_user_email, app_uuid=uid)
                        RunAppAsyncJob.create(
                            func="llmstack.apps.apis.run_slack_app",
                            args=[new_request, uid, input_data, source, app_data_obj.data, session_id, False],
                        ).add_to_queue()

        return DRFResponse(status=200)


def run_twilio_sms_app(request, uid, input_data, source, app_data, session_id, stream=False):
    TwilioViewSet._run(request, uid, input_data, source, app_data, session_id, stream)


class TwilioViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @staticmethod
    def _run(request, uid, input_data, source, app_data, session_id, stream=False):
        twilio_config = None
        app = App.objects.filter(uuid=uid).first()
        if app:
            app_owner = app.owner
            if app_owner:
                app_owner_profile = Profile.objects.filter(user=app_owner).first()
                if app_owner_profile:
                    twilio_config = (
                        TwilioIntegrationConfig().from_dict(
                            app.twilio_integration_config,
                            app_owner_profile.decrypt_value,
                        )
                        if app.twilio_integration_config
                        else None
                    )
        if twilio_config:
            response = APIViewSet().run_internal(
                request=request,
                app_uuid=uid,
                input_data=input_data,
                source=source,
                session_id=session_id,
                stream=stream,
                app_data=app_data,
            )

            reply_to = input_data.get("_request", {}).get("From")
            reply_from = input_data.get("_request", {}).get("To")
            response_text = (
                response.data.get("output", {}).get("output")
                or (" ".join(response.data.get("output", {}).get("errors", [])) or "An error occurred.")
                if response.status_code == 200
                else "An error occurred."
            )
            response_payload = {
                "To": reply_to,
                "From": reply_from,
                "Body": response_text,
            }
            account_sid = twilio_config.get("account_sid")
            url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

            prequests.post(
                url,
                data=response_payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                auth=(account_sid, twilio_config.get("auth_token")),
            )

    def handle_sms_request(self, request, uid):
        app = get_object_or_404(App, uuid=uuid.UUID(uid))
        app_data_obj = AppData.objects.filter(app_uuid=app.uuid, is_draft=False).order_by("-created_at").first()
        if not app_data_obj:
            return DRFResponse(status=404, data={"error": "App data not found"})

        app_owner_profile = get_object_or_404(Profile, user=app.owner)

        twilio_config = (
            TwilioIntegrationConfig().from_dict(
                app.twilio_integration_config,
                app_owner_profile.decrypt_value,
            )
            if app.twilio_integration_config
            else None
        )
        if twilio_config:
            session_id = (
                str(uuid.uuid5(uuid.NAMESPACE_URL, f'{str(uid)}-{request.data.get("From")}'))
                if request.data.get("From")
                else str(uuid.uuid4())
            )

            twilio_sms_text = request.data.get("Body", "").strip()
            input_data = {
                **dict(
                    zip(
                        list(
                            map(lambda x: x["name"], app_data_obj.data["input_fields"]),
                        ),
                        [twilio_sms_text] * len(app_data_obj.data["input_fields"]),
                    ),
                ),
                "_request": {
                    "ToCountry": request.data.get("ToCountry", ""),
                    "ToState": request.data.get("ToState", ""),
                    "SmsMessageSid": request.data.get("SmsMessageSid", ""),
                    "NumMedia": request.data.get("NumMedia", ""),
                    "ToCity": request.data.get("ToCity", ""),
                    "FromZip": request.data.get("FromZip", ""),
                    "SmsSid": request.data.get("SmsSid", ""),
                    "FromState": request.data.get("FromState", ""),
                    "SmsStatus": request.data.get("SmsStatus", ""),
                    "FromCity": request.data.get("FromCity", ""),
                    "Body": request.data.get("Body", ""),
                    "FromCountry": request.data.get("FromCountry", ""),
                    "To": request.data.get("To", ""),
                    "ToZip": request.data.get("ToZip", ""),
                    "NumSegments": request.data.get("NumSegments", ""),
                    "MessageSid": request.data.get("MessageSid", ""),
                    "AccountSid": request.data.get("AccountSid", ""),
                    "From": request.data.get("From", ""),
                    "ApiVersion": request.data.get("ApiVersion", ""),
                },
            }
            new_request = RequestFactory().post("/api/apps/{}/run".format(uid))
            new_request.user = AnonymousUser()
            new_request.data = {"input": input_data, "session_id": session_id}

            source = TwilioAppRunnerSource(app_uuid=uid, incoming_number=request.data.get("From"))

            RunAppAsyncJob.create(
                func="llmstack.apps.apis.run_twilio_sms_app",
                args=[new_request, uid, input_data, source, app_data_obj.data, session_id, False],
            ).add_to_queue()

        return DRFResponse(status=204, content_type="text/xml")

    def handle_voice_request(self, request, uid):
        # Get app and verify it exists
        app = get_object_or_404(App, uuid=uuid.UUID(uid))

        # Get app owner profile and twilio config
        app_owner_profile = get_object_or_404(Profile, user=app.owner)
        twilio_config = (
            TwilioIntegrationConfig().from_dict(
                app.twilio_integration_config,
                app_owner_profile.decrypt_value,
            )
            if app.twilio_integration_config
            else None
        )

        # TODO: Make sure the app is voice enabled

        if (
            twilio_config
            and request.data.get("To") in twilio_config.get("phone_numbers", [])
            and request.data.get("AccountSid") == twilio_config.get("account_sid")
        ):
            logger.info(f"wss://{request.get_host()}/ws/apps/{uid}/twiliovoice")

            # Generate TwiML response for websocket connection
            twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Connect>
                    <Stream url="wss://{request.get_host()}/ws/apps/{uid}/twiliovoice/{request.data.get('From')}" />
                </Connect>
            </Response>"""

            return HttpResponse(content=twiml_response, content_type="text/xml; charset=utf-8")

        return DRFResponse(status=403, data={"error": "Invalid Twilio configuration"})
