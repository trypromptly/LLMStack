import logging
import uuid

import requests
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response as DRFResponse
from rest_framework.views import APIView

from llmstack.apps.apis import AppViewSet
from llmstack.apps.models import App
from llmstack.apps.serializers import AppAsStoreAppSerializer
from llmstack.common.utils.utils import generate_checksum, vectorize_text

from .models import AppStoreApp, AppStoreAppAssets, filter_queryset_by_query
from .serializers import AppStoreAppSerializer

logger = logging.getLogger(__name__)


def download_file(url):
    """
    Returns mime_type, file_name, file_data
    """
    response = requests.get(url)
    response.raise_for_status()

    mime_type = response.headers.get("Content-Type")
    file_name = response.headers.get("Content-Disposition").split("filename=")[-1]
    file_data = response.content

    return mime_type, file_name, file_data


@sync_to_async
def _fetch_app(store_app_slug, user):
    """
    Fetches app and returns app_uuid, store_app_uuid and app_data
    """
    try:
        uuid.UUID(store_app_slug)
        app = App.objects.filter(
            uuid=store_app_slug,
        ).first()
        if app and user == app.owner or user.email in app.read_accessible_by:
            return str(app.uuid), None, None
    except ValueError:
        store_app = AppStoreApp.objects.filter(slug=store_app_slug).first()
        if store_app:
            return None, str(store_app.uuid), store_app.app_data
    except Exception as e:
        logger.error(f"Error fetching app with slug {store_app_slug}: {e}")

    return None, None, None


class AppStoreAppViewSet(viewsets.ModelViewSet):
    queryset = AppStoreApp.objects.all().order_by("-created_at")
    serializer_class = AppStoreAppSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    @staticmethod
    def create_or_update(app_data, obj=None):
        slug = app_data["slug"]

        if not obj and AppStoreApp.objects.filter(slug=slug).exists():
            raise Exception(f"App with slug {slug} already exists")

        if not obj:
            obj = AppStoreApp()
            obj.slug = app_data["slug"]

        # Handle icon
        if obj.app_data.get("icon", "") == app_data.get("icon", ""):
            obj.app_data = app_data

            if obj.name and obj.description:
                obj.search_vector = vectorize_text(obj.search_text)

            obj.save()
            return
        elif obj.icon and not obj.app_data.get("icon", ""):
            obj._delete_old_icon(uuid=obj.icon)
            obj._delete_old_icon(uuid=obj.icon128)
            obj._delete_old_icon(uuid=obj.icon256)
            obj._delete_old_icon(uuid=obj.icon512)

            obj.icon = None
            obj.icon128 = None
            obj.icon256 = None
            obj.icon512 = None

        if "icon" in app_data:
            if obj.icon:
                obj._delete_old_icon(uuid=obj.icon)
                obj.icon = None

            # Read icon data as data-uri from local path. If it is a url, download the file and read as data-uri
            icon_data = app_data["icon"]
            mime_type = "image/png"
            file_name = "icon.png"
            file_bytes = None

            if icon_data.startswith("http"):
                mime_type, file_name, file_bytes = download_file(icon_data)
            else:
                with open(icon_data, "rb") as f:
                    file_bytes = f.read()
                    file_name = icon_data.split("/")[-1]

            file_checksum = generate_checksum(file_bytes)

            icon_file_obj = AppStoreAppAssets.create_from_bytes(
                file_bytes,
                file_name,
                {"file_checksum": file_checksum, "mime_type": mime_type, "file_name": file_name},
                obj.uuid,
            )
            icon_file_obj.app_store_app_uuid = obj.uuid
            app_data["icon"] = str(icon_file_obj.uuid)
            obj.icon = app_data["icon"]

            if obj.icon128:
                obj._delete_old_icon(uuid=obj.icon128)
                obj.icon128 = None
            if obj.icon256:
                obj._delete_old_icon(uuid=obj.icon256)
                obj.icon256 = None
            if obj.icon512:
                obj._delete_old_icon(uuid=obj.icon512)
                obj.icon512 = None

            icon128_thumbnail, icon128_thumbnail_filename = obj._create_icon_thumbnail((128, 128))
            icon128_thumbnail_file_obj = AppStoreAppAssets.create_from_bytes(
                icon128_thumbnail,
                icon128_thumbnail_filename,
                {"mime_type": mime_type, "file_name": icon128_thumbnail_filename},
                obj.uuid,
            )
            icon128_thumbnail_file_obj.app_store_app_uuid = obj.uuid
            obj.icon128 = icon128_thumbnail_file_obj.uuid
            icon256_thumbnail, icon256_thumbnail_filename = obj._create_icon_thumbnail((256, 256))
            icon256_thumbnail_file_obj = AppStoreAppAssets.create_from_bytes(
                icon256_thumbnail,
                icon256_thumbnail_filename,
                {"mime_type": mime_type, "file_name": icon256_thumbnail_filename},
                obj.uuid,
            )
            icon128_thumbnail_file_obj.app_store_app_uuid = obj.uuid
            obj.icon256 = icon256_thumbnail_file_obj.uuid
            icon512_thumbnail, icon512_thumbnail_filename = obj._create_icon_thumbnail((512, 512))
            icon512_thumbnail_file_obj = AppStoreAppAssets.create_from_bytes(
                icon512_thumbnail,
                icon512_thumbnail_filename,
                {"mime_type": mime_type, "file_name": icon512_thumbnail_filename},
                obj.uuid,
            )
            icon512_thumbnail_file_obj.app_store_app_uuid = obj.uuid
            obj.icon512 = icon512_thumbnail_file_obj.uuid

        obj.app_data = app_data
        if obj.name and obj.description:
            obj.search_vector = vectorize_text(obj.search_text)
        obj.save()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return DRFResponse(serializer.data)

    def get(self, request, slug):
        try:
            """
            If this is a valid uuid, return the app with that uuid
            """
            uuid.UUID(slug)
            instance = App.objects.filter(
                uuid=slug,
            ).first()
            if instance and request.user == instance.owner or request.user.email in instance.read_accessible_by:
                serializer = AppAsStoreAppSerializer(instance)
                return DRFResponse(serializer.data)

            return DRFResponse(status=404)
        except ValueError:
            pass

        instance = AppStoreApp.objects.filter(slug=slug).first()
        if instance is None:
            return DRFResponse(status=404)

        serializer = self.get_serializer(instance)
        return DRFResponse(serializer.data)

    async def run_app_internal_async(self, slug, session_id, request_uuid, request):
        app_uuid, store_app_uuid, app_data = await _fetch_app(slug, request.user)

        if not app_uuid and not store_app_uuid:
            return DRFResponse(status=404)

        return await database_sync_to_async(AppViewSet().run_app_internal)(
            uid=app_uuid,
            session_id=session_id,
            request_uuid=request_uuid,
            request=request,
            preview=True,
            app_store_uuid=store_app_uuid,
            app_store_app_data=app_data,
        )

    async def get_app_runner_async(self, session_id, app_slug, source, request_user):
        from llmstack.apps.runner.app_runner import AppRunner
        from llmstack.base.models import Profile

        runner_user = request_user
        app_store_app = AppStoreApp.objects.filter(slug=app_slug).first()
        if app_store_app is None:
            return DRFResponse(status=404)

        app_data = app_store_app.app_data

        if not app_data:
            raise Exception("App not found for platform app")

        if runner_user is None or runner_user.is_anonymous:
            raise Exception("User not found")

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

    def get_app_runner(self, session_id, app_slug, source, request_user):
        from asgiref.sync import async_to_sync

        return async_to_sync(self.get_app_runner_async)(
            session_id,
            app_slug,
            source,
            request_user,
        )


class ListAppStoreCategories(APIView):
    permission_classes = [IsAuthenticated]
    method = ["GET"]

    @cache_page(60 * 60 * 12)
    def get(self, request, format=None):
        categories = []
        store_apps = AppStoreApp.objects.all()
        for app in store_apps:
            categories.extend([category.lower() for category in app.categories])

        # Remove duplicates
        categories = list(set(categories))

        fixed = [{"name": category.capitalize(), "slug": category} for category in categories]
        special = []
        special.append({"name": "Recommended", "slug": "recommended"})
        special.append({"name": "New", "slug": "new"})
        special.append({"name": "My Apps", "slug": "my-apps"})
        return DRFResponse(
            {
                "fixed": fixed,
                "special": special,
            }
        )


class AppStoreSearchViewSet(viewsets.ModelViewSet):
    serializer_class = AppStoreAppSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def list(self, request):
        total = AppStoreApp.objects.count()

        query = request.query_params.get("query")
        limit = request.query_params.get("limit", total)

        if not query:
            return DRFResponse(status=400)

        apps = AppStoreApp.objects.all()
        similar_queryset = filter_queryset_by_query(query, apps, top_k=limit)
        queryset = list(map(lambda x: x[0], similar_queryset))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return DRFResponse(serializer.data)


class AppStoreCategoryAppsViewSet(viewsets.ModelViewSet):
    queryset = AppStoreApp.objects.all().order_by("-created_at")
    serializer_class = AppStoreAppSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self, category_slug):
        store_apps = AppStoreApp.objects.all()
        return [x for x in store_apps if category_slug.lower() in x.categories]

    def list(self, request, slug):
        queryset = self.filter_queryset(self.get_queryset(slug))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return DRFResponse(serializer.data)


class AppStoreSpecialCategoryAppsViewSet(viewsets.ModelViewSet):
    serializer_class = AppStoreAppSerializer
    method = ["GET"]

    def get_permissions(self):
        return [IsAuthenticated()]

    @method_decorator(cache_page(60 * 60 * 12))
    def recommended_apps(self, request, slug):
        app = AppStoreApp.objects.filter(slug=slug).first()
        if not app:
            """
            Return new apps if app not found
            """
            return self.new_apps(request)

        total = AppStoreApp.objects.count()
        apps = AppStoreApp.objects.filter(~Q(slug=slug))
        similar_queryset = filter_queryset_by_query(app.search_text, apps, top_k=total - 1)

        queryset = list(map(lambda x: x[0], similar_queryset))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return DRFResponse(serializer.data)

    @method_decorator(cache_page(60 * 60 * 0.5))
    def new_apps(self, request):
        queryset = AppStoreApp.objects.filter().order_by("-created_at")
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return DRFResponse(serializer.data)

    @method_decorator(cache_page(60 * 60 * 0.5))
    def my_apps(self, request):
        queryset = App.objects.filter(
            Q(owner=request.user) | Q(read_accessible_by__contains=[request.user.email])
        ).order_by("-last_updated_at")
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AppAsStoreAppSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AppAsStoreAppSerializer(queryset, many=True)
        return DRFResponse(serializer.data)
