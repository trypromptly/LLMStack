import logging

from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response as DRFResponse

from llmstack.apps.models import AppDataAssets, AppSessionFiles

logger = logging.getLogger(__name__)


class AssetViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.request.method in ["GET"]:
            return [AllowAny()]
        else:
            return [IsAuthenticated()]

    def get(self, request, category, uuid, include_data=False, include_name=False):
        asset = self.get_asset_data(
            objref=f"objref://{category}/{uuid}",
            request_user=request.user,
            request_session=request.session,
            include_data=include_data,
            include_name=include_name,
        )
        if asset is None:
            return DRFResponse(status=404)

        return DRFResponse(asset)

    def get_by_objref(self, request, objref, include_data=False, include_name=False):
        asset = self.get_asset_data(
            objref, request.user, request.session, include_data=include_data, include_name=include_name
        )
        if asset is None:
            return DRFResponse(status=404)

        return DRFResponse(asset)

    def get_asset_data(self, objref, request_user, request_session=None, include_data=False, include_name=False):
        try:
            category, asset_uuid = objref.split("objref://")[1].split("/")

            model_cls = None
            if category == "sessionfiles":
                model_cls = AppSessionFiles
            elif category == "appdata":
                model_cls = AppDataAssets

            if not model_cls:
                return None

            asset = model_cls.objects.filter(uuid=asset_uuid).first()

            if asset is None or not model_cls.is_accessible(asset, request_user, request_session):
                return None

            response = {"url": asset.file.url}

            if "file_name" in asset.metadata:
                response["name"] = asset.metadata["file_name"]

            if "mime_type" in asset.metadata:
                response["type"] = asset.metadata["mime_type"]

            if "file_size" in asset.metadata:
                response["size"] = asset.metadata["file_size"]

            if include_data:
                response["data_uri"] = model_cls.get_asset_data_uri(asset, include_name=include_name)

            return response
        except Exception as e:
            logger.error(f"Failed to get asset data for objref {objref} with error: {e}")
            return None
