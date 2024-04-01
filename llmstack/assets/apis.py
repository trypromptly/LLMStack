import logging

from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response as DRFResponse

from llmstack.apps.models import AppSessionFiles

logger = logging.getLogger(__name__)


class AssetViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.request.method in ["GET"]:
            return [AllowAny()]
        else:
            return [IsAuthenticated()]

    def get(self, request, category, uuid, include_data=False, include_name=False):
        model_cls = None
        if category == "sessionfiles":
            model_cls = AppSessionFiles

        if not model_cls:
            return DRFResponse(status=403)

        asset = get_object_or_404(model_cls, uuid=uuid)

        if not model_cls.is_accessible(asset, request.user, request.session):
            return DRFResponse(status=403)

        response = {"url": asset.file.url}

        if "file_name" in asset.metadata:
            response["name"] = asset.metadata["file_name"]

        if "mime_type" in asset.metadata:
            response["type"] = asset.metadata["mime_type"]

        if "file_size" in asset.metadata:
            response["size"] = asset.metadata["file_size"]

        if "include_data" in request.query_params or include_data:
            should_include_name = include_name or "include_name" in request.query_params

            response["data_uri"] = model_cls.get_asset_data_uri(asset, include_name=should_include_name)

        return DRFResponse(response)

    def get_by_objref(self, request, objref, include_data=False, include_name=False):
        try:
            url_parts = objref.split("objref://")[1].split("/")
            return self.get(request, url_parts[0], url_parts[1], include_data=include_data, include_name=include_name)
        except Exception as e:
            logger.error(f"Failed to get asset for objref {objref} with error: {e}")
            return DRFResponse(status=400)
