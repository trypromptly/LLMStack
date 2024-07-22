import logging
import uuid

from django.contrib.postgres.fields import ArrayField as PGArrayField
from django.db import models

from llmstack.assets.models import Assets
from llmstack.common.utils.utils import vectorize_text

logger = logging.getLogger(__name__)


class AppStoreAppAssets(Assets):
    def select_storage():
        from django.core.files.storage import storages

        return storages["assets"]

    def appstore_upload_to(instance, filename):
        return "/".join(["appstore", str(instance.ref_id), filename])

    ref_id = models.UUIDField(help_text="UUID of the app store app this asset belongs to", blank=True, null=False)
    file = models.FileField(
        storage=select_storage,
        upload_to=appstore_upload_to,
        null=True,
        blank=True,
    )

    @property
    def category(self):
        return "appstore"


class AppStoreApp(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=100, null=False, blank=False, unique=True)
    app_data = models.JSONField(null=True, blank=True, default=dict)
    icon = models.UUIDField(null=True, blank=True, default=None)
    icon128 = models.UUIDField(null=True, blank=True, default=None)
    icon256 = models.UUIDField(null=True, blank=True, default=None)
    icon512 = models.UUIDField(null=True, blank=True, default=None)
    rank = models.IntegerField(default=0, help_text="Rank of the instance")
    is_archived = models.BooleanField(default=False, help_text="Is the app archived")
    search_vector = PGArrayField(models.FloatField(), default=list, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.slug

    @property
    def version(self):
        return self.app_data.get("version", "") if self.app_data else ""

    @property
    def name(self):
        return self.app_data.get("name", "") if self.app_data else ""

    @property
    def description(self):
        return self.app_data.get("description", "") if self.app_data else ""

    @property
    def search_text(self):
        return f"Name: {self.name} Description: {self.description} Categories: {', '.join(self.categories)}"

    @property
    def categories(self):
        return self.app_data.get("categories", []) if self.app_data else []

    @property
    def icon_url(self):
        if self.icon:
            file_obj = AppStoreAppAssets.objects.filter(uuid=self.icon).first()
            return file_obj.file.url if file_obj else None
        return None

    @property
    def icon128_url(self):
        if self.icon128:
            file_obj = AppStoreAppAssets.objects.filter(uuid=self.icon128).first()
            return file_obj.file.url if file_obj else None
        return None

    @property
    def icon256_url(self):
        if self.icon256:
            file_obj = AppStoreAppAssets.objects.filter(uuid=self.icon256).first()
            return file_obj.file.url if file_obj else None
        return None

    @property
    def icon512_url(self):
        if self.icon512:
            file_obj = AppStoreAppAssets.objects.filter(uuid=self.icon512).first()
            return file_obj.file.url if file_obj else None
        return None

    def _create_icon_thumbnail(self, size):
        from PIL import Image

        def _image_to_thumbnail(image, size, format="PNG"):
            from io import BytesIO

            image.thumbnail(size)
            thumb_io = BytesIO()
            image.save(thumb_io, format=format)
            # Get the thumbnail content as bytes
            thumb_io.seek(0)
            thumbnail_bytes = thumb_io.getvalue()
            return thumbnail_bytes

        if self.icon:
            file_obj = AppStoreAppAssets.objects.filter(uuid=self.icon).first()
            icon_filename = file_obj.file.name.split("/")[-1].split(".")[0]
            with Image.open(file_obj.file) as image:
                thumbnail_bytes = _image_to_thumbnail(image, size, "PNG")
                return thumbnail_bytes, f"{icon_filename}_{size[0]}x{size[1]}_thumb.png"

        return None

    @property
    def owner(self):
        return None

    def _delete_old_icon(self, uuid):
        if not uuid:
            return

        file_obj = AppStoreAppAssets.objects.filter(uuid=uuid).first()
        if file_obj:
            file_obj.delete()

    def archive(self, *args, **kwargs):
        self.is_archived = True
        self.save(args, kwargs)

    def save(self, *args, **kwargs):
        self.slug = self.slug.lower()
        super(AppStoreApp, self).save(*args, **kwargs)


def filter_queryset_by_query(query, queryset, vector_field_name="search_vector", top_k=3):
    import faiss
    import numpy as np

    base_vector = np.array(vectorize_text(query))
    # Retrieve all vectors from the queryset
    all_vectors = np.array([getattr(obj, vector_field_name) for obj in queryset])

    # Build an index
    index = faiss.IndexFlatL2(base_vector.size)
    index.add(all_vectors)

    # Search for the most similar vectors
    distances, idx = index.search(np.expand_dims(base_vector, axis=0), top_k)

    # Get the IDs and similarity scores of the most similar objects
    similar_objects = [(queryset[int(i)], float(dist)) for i, dist in zip(idx[0], distances[0])]

    # Order the queryset based on the similarity scores
    ordered_queryset = sorted(similar_objects, key=lambda x: x[1])
    return ordered_queryset
