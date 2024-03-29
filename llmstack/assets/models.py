import base64
import uuid

from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver


class Assets(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, help_text="UUID of the asset")
    ref_id = None
    file = None
    metadata = models.JSONField(
        default=dict,
        help_text="Metadata for the asset",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

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
    def is_accessible(request, asset):
        return False

    class Meta:
        abstract = True


@receiver(pre_delete)
def delete_file_on_delete(sender, instance, **kwargs):
    if issubclass(sender, Assets) and instance.file:
        instance.file.delete(False)
