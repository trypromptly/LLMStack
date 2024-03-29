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

    def get(self, request, category, uuid):
        model_cls = None
        if category == "sessionfiles":
            model_cls = AppSessionFiles

        if not model_cls:
            return DRFResponse(status=403)

        asset = get_object_or_404(model_cls, uuid=uuid)

        if not model_cls.is_accessible(request, asset):
            return DRFResponse(status=403)

        response = {"url": asset.file.url}

        if "file_name" in asset.metadata:
            response["name"] = asset.metadata["file_name"]

        if "mime_type" in asset.metadata:
            response["type"] = asset.metadata["mime_type"]

        if "file_size" in asset.metadata:
            response["size"] = asset.metadata["file_size"]

        return DRFResponse(response)
