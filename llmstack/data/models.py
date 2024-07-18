import logging
import uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.timezone import now

from llmstack.assets.models import Assets
from llmstack.base.models import Profile, VectorstoreEmbeddingEndpoint
from llmstack.common.utils.provider_config import get_matched_provider_config
from llmstack.events.apis import EventsViewSet

logger = logging.getLogger(__name__)


class RefreshFreqeuncy(models.TextChoices):
    DAILY = "DAILY", "Daily"
    WEEKLY = "WEEKLY", "Weekly"
    MONTHLY = "MONTHLY", "Monthly"
    YEARLY = "YEARLY", "Yearly"
    ONCE = "ONCE", "Once"


class DataSourceEntryStatus(models.TextChoices):
    PROCESSING = "PROCESSING", "Processing"
    READY = "READY", "Ready"
    FAILED = "FAILED", "Failed"
    MARKED_FOR_DELETION = "MARKED_FOR_DELETION", "Marked for deletion"


class DataSourceVisibility(models.IntegerChoices):
    PRIVATE = 0, "Private"
    ORGANIZATION = 1, "Organization"


class DataSourceType(models.Model):
    """
    Data source allows us to support different ways of getting data into the system
    """

    name = models.CharField(
        max_length=100,
        help_text="Name of the data source type",
    )
    slug = models.CharField(
        max_length=50,
        default="",
        help_text="Slug of the data source type",
    )
    description = models.TextField(
        default="",
        blank=True,
        help_text="Description of the data source type",
    )
    is_external_datasource = models.BooleanField(
        default=False,
        help_text="Is this an external data source?",
    )

    def __str__(self):
        return self.name


class DataSource(models.Model):
    """
    Individual data source
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        help_text="UUID of the data source",
        unique=True,
    )
    type = models.ForeignKey(
        DataSourceType,
        on_delete=models.DO_NOTHING,
        help_text="Type of the data source",
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        help_text="Owner of the data source",
    )
    name = models.CharField(
        max_length=100,
        help_text="Name of the data source",
    )
    size = models.IntegerField(
        default=0,
        help_text="Size of the data source in bytes",
    )
    visibility = models.PositiveSmallIntegerField(
        default=DataSourceVisibility.PRIVATE,
        choices=DataSourceVisibility.choices,
        help_text="Visibility of the data source",
    )
    config = models.JSONField(
        default=dict,
        help_text="Config for the data source",
    )
    created_at = models.DateTimeField(
        help_text="Time when the data source was created",
        default=now,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Time when the data source was updated",
    )

    def __str__(self):
        return self.name + " (" + self.type.name + ")" + " - " + str(self.owner)

    @property
    def profile(self):
        return Profile.objects.get(user=self.owner)

    @property
    def type_slug(self):
        return self.config.get("type_slug", "")

    @property
    def source_schema(self):
        source_cls = self.source_cls
        if source_cls:
            return source_cls.get_schema()
        return {}

    @property
    def source_cls(self):
        from llmstack.data.sources.utils import get_source_cls
        from llmstack.data.yaml_loader import get_data_pipeline_template_by_slug

        pipeline_template = get_data_pipeline_template_by_slug(self.type_slug)
        return get_source_cls(pipeline_template.pipeline.source.slug, pipeline_template.pipeline.source.provider_slug)

    @property
    def destination_schema(self):
        destination_cls = self.destination_cls
        if destination_cls:
            return destination_cls.get_schema()
        return {}

    @property
    def destination_cls(self):
        from django.conf import settings

        from llmstack.data.destinations.utils import get_destination_cls
        from llmstack.data.destinations.vector_stores.legacy_chromadb import (
            PromptlyLegacyChromaDBVectorStoreConfiguration,
        )
        from llmstack.data.destinations.vector_stores.legacy_weaviate import (
            PromptlyLegacyWeaviateVectorStoreConfiguration,
        )
        from llmstack.data.yaml_loader import get_data_pipeline_template_by_slug

        pipeline_template = get_data_pipeline_template_by_slug(self.type_slug)

        # For Legacy Data Sources
        if pipeline_template.pipeline.destination is None and self.type_slug in [
            "csv_file",
            "file",
            "pdf",
            "gdrive_file",
            "text",
            "url",
        ]:
            if settings.VECTOR_DATABASES.get("default")["ENGINE"] == "weaviate":
                return PromptlyLegacyWeaviateVectorStoreConfiguration
            elif settings.VECTOR_DATABASES.get("default")["ENGINE"] == "chroma":
                return PromptlyLegacyChromaDBVectorStoreConfiguration

        return get_destination_cls(
            pipeline_template.pipeline.source.slug, pipeline_template.pipeline.source.provider_slug
        )

    @property
    def destination_text_content_key(self):
        if not self.config.get("destination_data") and self.type_slug in [
            "csv_file",
            "file",
            "pdf",
            "gdrive_file",
            "text",
            "url",
        ]:
            return "page_content" if self.type_slug == "url" else "content"
        return None

    @property
    def destination_data(self):
        from django.conf import settings

        data = {}
        if self.config.get("destination_data"):
            data = self.config.get("destination_data")
        elif self.type_slug in ["csv_file", "file", "pdf", "gdrive_file", "text", "url"]:
            # For Legacy Data Sources
            content_key = self.destination_text_content_key
            if settings.VECTOR_DATABASES.get("default")["ENGINE"] == "weaviate":
                data = {
                    "type": "promptly_legacy_weaviate",
                    "url": self.profile.weaviate_url,
                    "host": None,
                    "http_port": None,
                    "grpc_port": None,
                    "embeddings_rate_limit": None,
                    "embeddings_batch_size": None,
                    "additional_headers": None,
                    "api_key": self.profile.weaviate_api_key,
                    "index_name": "Datasource_" + str(self.uuid).replace("-", "_"),
                    "text_key": content_key,
                    "text2vec_openai_config": self.profile.weaviate_text2vec_config,
                }
                if self.profile.vectostore_embedding_endpoint == VectorstoreEmbeddingEndpoint.OPEN_AI:
                    openai_provider_config = get_matched_provider_config(
                        provider_configs=self.profile.get_vendor_env().get("provider_configs", {}),
                        provider_slug="openai",
                    )
                    data["additional_headers"] = {"X-OpenAI-Api-Key": openai_provider_config.api_key}
                else:
                    azure_provider_config = get_matched_provider_config(
                        provider_configs=self.profile.get_vendor_env().get("provider_configs", {}),
                        provider_slug="azure",
                    )

                    data["additional_headers"] = {"X-Azure-Api-Key": azure_provider_config.api_key}

            elif settings.VECTOR_DATABASES.get("default")["ENGINE"] == "chroma":
                data = {
                    "type": "promptly_legacy_chromadb",
                    "path": settings.VECTOR_DATABASES.get("default", {}).get("NAME", "chromadb"),
                    "settings": {"anonymized_telemetry": False, "is_persistent": True},
                    "index_name": "Datasource_" + str(self.uuid).replace("-", "_"),
                    "text_key": content_key,
                }

        return data

    @property
    def transformation_schema(self):
        return {}

    @property
    def transformation_cls(self):
        return None

    @property
    def transformation_data(self):
        return {}

    def create_data_pipeline(self):
        from llmstack.data.pipeline import DataPipeline

        return DataPipeline(self)


class DataSourceEntry(models.Model):
    """
    Individual file for a data source
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        help_text="UUID of the data source file",
        unique=True,
    )
    datasource = models.ForeignKey(
        DataSource,
        on_delete=models.DO_NOTHING,
        help_text="Data source",
    )
    config = models.JSONField(
        default=dict,
        help_text="Config for the data source entry",
    )
    name = models.CharField(
        max_length=2048,
        help_text="Name of the data source file",
        blank=True,
        default="",
    )
    size = models.IntegerField(
        default=0,
        help_text="Size of the entry in bytes",
    )
    status = models.CharField(
        default=DataSourceEntryStatus.PROCESSING,
        max_length=100,
        choices=DataSourceEntryStatus.choices,
        help_text="Status of the data source entry",
    )
    refresh_frequency = models.CharField(
        default=RefreshFreqeuncy.ONCE,
        max_length=100,
        choices=RefreshFreqeuncy.choices,
        help_text="Refresh frequency of the data source entry",
    )
    created_at = models.DateTimeField(
        help_text="Time when the data source file was created",
        default=now,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Time when the data source file was updated",
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.old_size = self.size
        self.owner_id = self.datasource.owner

    def user_can_read(self, user) -> bool:
        if self.datasource.visibility == DataSourceVisibility.PRIVATE:
            return self.datasource.owner == user
        elif self.datasource.visibility == DataSourceVisibility.ORGANIZATION:
            return (
                self.datasource.owner == user
                or Profile.objects.get(
                    user=self.datasource.owner,
                ).organization
                == Profile.objects.get(
                    user=user,
                ).organization
            )
        return False


@receiver(post_save, sender=DataSourceEntry)
def register_data_change(sender, instance: DataSourceEntry, **kwargs):
    if instance.old_size != instance.size:
        # The datasource entry size has changed
        EventsViewSet().create(
            topic="datasource_entries.update",
            event_data={
                "operation": "save",
                "uuid": str(instance.uuid),
                "old_size": instance.old_size,
                "size": instance.size,
                "owner": instance.owner_id,
            },
        )


@receiver(post_delete, sender=DataSourceEntry)
def register_data_delete(sender, instance: DataSourceEntry, **kwargs):
    if instance.old_size != 0:
        # The datasource entry size has changed
        EventsViewSet().create(
            topic="datasource_entries.update",
            event_data={
                "operation": "delete",
                "uuid": str(instance.uuid),
                "old_size": instance.size,
                "size": 0,
                "owner": instance.owner_id,
            },
        )


class DataSourceEntryFiles(Assets):
    def select_storage():
        from django.core.files.storage import storages

        return storages["assets"]

    def datasource_upload_to(instance, filename):
        return "/".join(["datasource_entries", str(instance.ref_id), filename])

    ref_id = models.UUIDField(help_text="UUID of the datasource entry this file belongs to", blank=True, null=False)
    file = models.FileField(
        storage=select_storage,
        upload_to=datasource_upload_to,
        null=True,
        blank=True,
    )

    @property
    def category(self):
        return "datasource_entries"
