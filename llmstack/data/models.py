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
    def vector_store_config(self):
        content_key = "text"
        vector_store = self.config.get("vector_store", {})
        if not vector_store:
            content_key = "content"
            # For Legacy Data Sources
            from django.conf import settings

            if self.type_slug == "csv_file":
                content_key = "content"
            elif self.type_slug == "file":
                content_key = "content"
            elif self.type_slug == "pdf":
                content_key = "content"
            elif self.type_slug == "gdrive_file":
                content_key = "content"
            elif self.type_slug == "text":
                content_key = "content"
            elif self.type_slug == "url":
                content_key = "page_content"

            if settings.VECTOR_DATABASES.get("default")["ENGINE"] == "weaviate":
                vector_store = {
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
                    vector_store["additional_headers"] = {"X-OpenAI-Api-Key": openai_provider_config.api_key}
                else:
                    azure_provider_config = get_matched_provider_config(
                        provider_configs=self.profile.get_vendor_env().get("provider_configs", {}),
                        provider_slug="azure",
                    )

                    vector_store["additional_headers"] = {"X-Azure-Api-Key": azure_provider_config.api_key}
            elif settings.VECTOR_DATABASES.get("default")["ENGINE"] == "chroma":
                vector_store = {
                    "type": "promptly_legacy_chromadb",
                    "path": settings.VECTOR_DATABASES.get("default", {}).get("NAME", "chromadb"),
                    "settings": {"anonymized_telemetry": False, "is_persistent": True},
                    "index_name": "Datasource_" + str(self.uuid).replace("-", "_"),
                    "text_key": content_key,
                }

        return vector_store

    @property
    def default_destination_request_data(self):
        from django.conf import settings

        content_key = "text"
        destination_request_data = {}
        content_key = "content"

        if self.type_slug == "url":
            content_key = "page_content"

        if settings.VECTOR_DATABASES.get("default")["ENGINE"] == "weaviate":
            destination_request_data = {
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
                destination_request_data["additional_headers"] = {"X-OpenAI-Api-Key": openai_provider_config.api_key}
            else:
                azure_provider_config = get_matched_provider_config(
                    provider_configs=self.profile.get_vendor_env().get("provider_configs", {}),
                    provider_slug="azure",
                )

                destination_request_data["additional_headers"] = {"X-Azure-Api-Key": azure_provider_config.api_key}
        elif settings.VECTOR_DATABASES.get("default")["ENGINE"] == "chroma":
            destination_request_data = {
                "type": "promptly_legacy_chromadb",
                "path": settings.VECTOR_DATABASES.get("default", {}).get("NAME", "chromadb"),
                "settings": {"anonymized_telemetry": False, "is_persistent": True},
                "index_name": "Datasource_" + str(self.uuid).replace("-", "_"),
                "text_key": content_key,
            }

        return destination_request_data

    @property
    def source_config(self):
        from llmstack.data.yaml_loader import get_data_pipelines_from_contrib

        source_config = None

        data_pipelines = get_data_pipelines_from_contrib()
        for pipeline in data_pipelines:
            if pipeline.slug == self.type.slug:
                source_config = pipeline.pipeline.source
        return source_config

    @property
    def transformations_config(self):
        from llmstack.data.yaml_loader import get_data_pipelines_from_contrib

        transformations_config = None

        data_pipelines = get_data_pipelines_from_contrib()
        for pipeline in data_pipelines:
            if pipeline.slug == self.type.slug:
                transformations_config = pipeline.pipeline.transformations
        return transformations_config

    @property
    def destination_config(self):
        from django.conf import settings

        from llmstack.data.yaml_loader import get_data_pipelines_from_contrib

        destination_config = None

        data_pipelines = get_data_pipelines_from_contrib()
        for pipeline in data_pipelines:
            if pipeline.slug == self.type.slug:
                destination_config = pipeline.pipeline.destination

        if destination_config is None and self.type_slug in ["csv_file", "file", "pdf", "gdrive_file", "text", "url"]:
            # For Legacy Data Sources
            from llmstack.data.schemas import BaseProcessorBlock

            if settings.VECTOR_DATABASES.get("default")["ENGINE"] == "weaviate":
                return BaseProcessorBlock(slug="promptly_legacy_weaviate", provider_slug="promptly")
            elif settings.VECTOR_DATABASES.get("default")["ENGINE"] == "chroma":
                return BaseProcessorBlock(slug="promptly_legacy_chromadb", provider_slug="promptly")

        return destination_config


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
