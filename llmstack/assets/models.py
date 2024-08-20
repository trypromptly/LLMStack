import base64
import uuid

import requests
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver


class Assets(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, help_text="UUID of the asset", unique=True)
    ref_id = None
    file = None
    metadata = models.JSONField(
        default=dict,
        help_text="Metadata for the asset",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def category(self):
        raise NotImplementedError

    @classmethod
    def create_from_bytes(cls, file_bytes, filename, metadata=None, ref_id=""):
        from django.core.files.base import ContentFile

        asset = cls(ref_id=ref_id)
        asset.file.save(filename, ContentFile(file_bytes))
        bytes_size = len(file_bytes)
        asset.metadata = {**metadata, "file_size": bytes_size}
        asset.save()
        return asset

    @classmethod
    def create_from_data_uri(cls, data_uri, metadata={}, ref_id=""):
        from llmstack.common.utils.utils import validate_parse_data_uri

        mime_type, file_name, file_data = validate_parse_data_uri(data_uri)
        file_bytes = base64.b64decode(file_data)
        return cls.create_from_bytes(
            file_bytes, file_name, {**metadata, "mime_type": mime_type, "file_name": file_name}, ref_id=ref_id
        )

    @classmethod
    def create_from_url(cls, url, metadata={}, ref_id=""):
        # Download the file from the URL and create an asset
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return None

        # Get the filename and mime type from the response headers
        file_name = url.split("://")[-1].split("?")[0].split("/")[-1]
        content_disposition = response.headers.get("content-disposition", "")
        content_disposition_split = content_disposition.split("filename=")
        if content_disposition_split and len(content_disposition_split) > 1:
            file_name = content_disposition.split("filename=")[1].strip()

        mime_type = response.headers.get("content-type", "application/octet-stream")

        return cls.create_from_bytes(
            response.content, file_name, {**metadata, "mime_type": mime_type, "file_name": file_name}, ref_id=ref_id
        )

    def update_file(self, file_bytes, filename):
        from django.core.files.base import ContentFile

        self.file.delete()
        self.file.save(filename, ContentFile(file_bytes))
        bytes_size = len(file_bytes)
        self.metadata = {**self.metadata, "file_size": bytes_size}
        self.save()
        return self

    @classmethod
    def create_asset(cls, metadata, ref_id, streaming=False):
        asset = cls(ref_id=ref_id)
        asset.metadata = metadata or {}

        if streaming:
            asset.metadata["streaming"] = True

        asset.save()
        return asset

    @classmethod
    def create_streaming_asset(cls, metadata, ref_id):
        return cls.create_asset(metadata, ref_id, streaming=True)

    @property
    def objref(self) -> str:
        return f"objref://{self.category}/{self.uuid}"

    def finalize_streaming_asset(self, file_bytes):
        from django.core.files.base import ContentFile

        file_name = self.metadata.get("file_name", str(uuid.uuid4()))

        # If the filename doesn't have an extension, add one based on the mime_type
        if "." not in file_name:
            # Get the extension from the mime type
            mime_type = self.metadata.get("mime_type", "application/octet-stream")
            extension = mime_type.split("/")[-1]

            # Add the extension to the filename
            file_name = f"{file_name}.{extension}"

        self.file.save(file_name, ContentFile(file_bytes))
        bytes_size = len(file_bytes)
        self.metadata = {**self.metadata, "file_size": bytes_size}
        self.metadata["streaming"] = False
        self.save()
        return self

    @classmethod
    def is_accessible(asset, request_user, request_session):
        return False

    @classmethod
    def get_asset_data_uri(cls, asset, include_name=False):
        if not asset:
            return None

        file_data = None
        if asset.file:
            with asset.file.open("rb") as f:
                file_data = f.read()

        if file_data:
            file_mime_type = asset.metadata.get("mime_type", "application/octet-stream")
            file_name = asset.metadata.get("file_name", "")
            if include_name:
                return f"data:{file_mime_type};name={file_name};base64,{base64.b64encode(file_data).decode('utf-8')}"
            return f"data:{asset.metadata['mime_type']};base64,{base64.b64encode(file_data).decode('utf-8')}"

        return None

    class Meta:
        abstract = True


@receiver(pre_delete)
def delete_file_on_delete(sender, instance, **kwargs):
    if issubclass(sender, Assets) and instance.file:
        instance.file.delete(False)
