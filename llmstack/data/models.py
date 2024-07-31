import logging
import uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.timezone import now

from llmstack.assets.models import Assets
from llmstack.base.models import Profile
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
    def pipeline_obj(self):
        from llmstack.data.schemas import PipelineBlock

        if self.config.get("pipeline"):
            return PipelineBlock(**self.config.get("pipeline"))

        return None

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
    def pipeline(self):
        return self.config.get("pipeline", {})

    def create_data_ingestion_pipeline(self):
        from llmstack.data.pipeline import DataIngestionPipeline

        return DataIngestionPipeline(self)

    def create_data_query_pipeline(self):
        from llmstack.data.pipeline import DataQueryPipeline

        return DataQueryPipeline(self)


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

    @classmethod
    def is_accessible(asset, request_user, request_session):
        return True
