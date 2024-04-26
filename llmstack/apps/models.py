import base64
import logging
import uuid

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField as PGArrayField
from django.core.files import storage
from django.core.files.base import ContentFile
from django.db import connection, models
from django.db.models.signals import pre_save
from django.dispatch import receiver

from llmstack.apps.integration_configs import (
    DiscordIntegrationConfig,
    SlackIntegrationConfig,
    TwilioIntegrationConfig,
    WebIntegrationConfig,
)
from llmstack.assets.models import Assets
from llmstack.base.models import Profile
from llmstack.common.utils.db_models import ArrayField
from llmstack.processors.models import Endpoint

logger = logging.getLogger(__name__)

public_file_storage = storage.storages["public_assets"]


class AppVisibility(models.IntegerChoices):
    PRIVATE = 0, "Private"  # only the owner of the app and listed emails can access the app
    # only members of the organization can access the app
    ORGANIZATION = 1, "Organization"
    UNLISTED = 2, "Unlisted"  # anyone with the link can access the app
    PUBLIC = 3, "Public"  # anyone can access the app and


class AppAccessPermission(models.IntegerChoices):
    """
    App access permission when shared in private mode
    """

    READ = 0, "Read"
    WRITE = 1, "Write"


class AppType(models.Model):
    """
    App type dictates the rendering, input and output formats for the app
    """

    name = models.CharField(max_length=100, help_text="Name of the app type")
    slug = models.CharField(
        max_length=50,
        default="",
        help_text="Slug of the app type",
    )
    description = models.TextField(
        default="",
        blank=True,
        help_text="Description of the app type",
    )
    slug = models.CharField(
        max_length=100,
        unique=True,
        help_text="Slug of the app type",
        default="",
    )

    def __str__(self) -> str:
        return self.name


class AppRunGraphEntry(models.Model):
    """
    Each graph entry is an edge in the DAG of the app run graph
    """

    owner = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        help_text="Owner of the node",
        default=None,
        null=True,
    )
    entry_endpoint = models.ForeignKey(
        Endpoint,
        on_delete=models.DO_NOTHING,
        help_text="Start endpoint of the edge. Null for first entry",
        related_name="entry_endpoint",
        null=True,
        default=None,
        blank=True,
    )
    exit_endpoint = models.ForeignKey(
        Endpoint,
        on_delete=models.DO_NOTHING,
        help_text="End endpoint of the edge. Null for last entry",
        related_name="exit_endpoint",
        null=True,
        default=None,
        blank=True,
    )
    logic_gate = models.TextField(
        default="",
        blank=True,
        help_text="Logic gate to be applied on the edge specified as Jinja2 template over output schema of entry endpoint",
    )
    data_transformer = models.TextField(
        default="",
        blank=True,
        help_text="Data transformer to be applied on the edge specified as Jinja2 template over output schema of entry endpoint and input of exit endpoint",
    )


class AppTemplateCategory(models.Model):
    """
    App template category
    """

    name = models.CharField(
        max_length=100,
        help_text="Name of the app template category",
    )
    description = models.TextField(
        default="",
        blank=True,
        help_text="Description of the app template category",
    )
    slug = models.CharField(
        max_length=100,
        unique=True,
        help_text="Slug of the app template category",
        default="",
    )

    def __str__(self) -> str:
        return self.slug


class AppTemplate(models.Model):
    """
    App template used to create an app
    """

    name = models.CharField(
        max_length=100,
        help_text="Name of the app template",
    )
    description = models.TextField(
        default="",
        blank=True,
        help_text="Description of the app template",
    )
    slug = models.CharField(
        max_length=100,
        unique=True,
        help_text="Slug of the app template",
        default="",
    )
    app_uuid = models.UUIDField(
        default=uuid.uuid4,
        help_text="UUID of the app this template is based on. App is used to get the processor chain etc.,",
    )
    categories = models.ManyToManyField(
        AppTemplateCategory,
        help_text="Categories of the app template",
        blank=True,
        default=None,
    )
    example_app_uuid = models.CharField(
        max_length=100,
        help_text="UUID of the example app for this template",
        default="",
        blank=True,
    )
    order = models.IntegerField(
        default=0,
        help_text="Order of the app template in the category",
    )

    def __str__(self) -> str:
        return self.slug


class App(models.Model):
    """
    Each App will have a run_graph which will be a DAG of Endpoint nodes with a logic gate followed by a DataTransformer node as edges.
    """

    name = models.CharField(max_length=100, help_text="Name of the app")
    published_uuid = models.UUIDField(
        default=uuid.uuid4,
        help_text="Identifier for the app when published",
        null=True,
        blank=True,
        unique=True,
    )
    store_uuid = models.UUIDField(
        help_text="Identifier for the app in the store",
        null=True,
        blank=True,
    )
    uuid = models.UUIDField(
        default=uuid.uuid4,
        help_text="Identifier for the app",
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        help_text="Owner of the app",
    )
    type = models.ForeignKey(
        AppType,
        on_delete=models.DO_NOTHING,
        help_text="Type of the app",
    )
    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Config for this app based on the app type",
    )
    input_schema = models.JSONField(
        blank=True,
        help_text="Input fields for this app in JSON schema format",
        default=dict,
        null=True,
    )
    input_ui_schema = models.JSONField(
        blank=True,
        help_text="UI schema for input_schema",
        default=dict,
        null=True,
    )
    output_template = models.JSONField(
        blank=True,
        help_text="Output template for this app in JSON format. We support markdown, JSON etc., as keys",
        default=dict,
        null=True,
    )
    description = models.TextField(
        default="",
        blank=True,
        help_text="Description of the app. Support markdown.",
    )
    run_graph = models.ManyToManyField(
        AppRunGraphEntry,
        help_text="Run graph of the app",
    )
    data_transformer = models.TextField(
        default="",
        blank=True,
        help_text="Data transformer to be applied before calling the first node of the run graph",
    )
    template = models.ForeignKey(
        AppTemplate,
        on_delete=models.DO_NOTHING,
        help_text="Template used for this app",
        default=None,
        null=True,
        blank=True,
    )
    template_slug = models.CharField(
        max_length=100,
        help_text="Slug of the template used for this app",
        default=None,
        null=True,
        blank=True,
    )
    is_public = models.BooleanField(
        default=True,
        help_text="Whether the app is public or not",
    )
    is_published = models.BooleanField(
        default=False,
        help_text="Whether the app is published or not",
        blank=True,
    )
    is_cloneable = models.BooleanField(
        default=False,
        help_text="Whether the app is cloneable or not",
        blank=False,
    )
    domain = models.CharField(
        default=None,
        max_length=2000,
        blank=True,
        null=True,
        help_text="Custom domain associated with the app",
    )
    visibility = models.PositiveSmallIntegerField(
        default=AppVisibility.PUBLIC,
        choices=AppVisibility.choices,
        help_text="Visibility of the app",
    )
    accessible_by = (
        PGArrayField(
            models.CharField(
                max_length=320,
            ),
            default=list,
            help_text="List of user emails or domains who can access the app",
            blank=True,
        )
        if connection.vendor == "postgresql"
        else ArrayField(
            null=True,
            help_text="List of user emails or domains who can access the app",
            blank=True,
        )
    )
    read_accessible_by = (
        PGArrayField(
            models.CharField(
                max_length=320,
            ),
            default=list,
            help_text="List of user emails or domains who can access the app",
            blank=True,
        )
        if connection.vendor == "postgresql"
        else ArrayField(
            null=True,
            help_text="List of user emails or domains who can access the app",
            blank=True,
        )
    )
    write_accessible_by = (
        PGArrayField(
            models.CharField(
                max_length=320,
            ),
            default=list,
            help_text="List of user emails or domains who can modify the app",
            blank=True,
        )
        if connection.vendor == "postgresql"
        else ArrayField(
            null=True,
            help_text="List of user emails or domains who can modify the app",
            blank=True,
        )
    )
    access_permission = models.PositiveSmallIntegerField(
        default=AppAccessPermission.READ,
        choices=AppAccessPermission.choices,
        help_text="Permission for users who can access the app",
    )
    last_modified_by = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        help_text="Last modified by",
        default=None,
        null=True,
        related_name="last_modified_by",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Time at which the app was created",
        blank=True,
        null=True,
    )
    last_updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Time at which the app was last updated",
        blank=True,
        null=True,
    )
    web_integration_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Embed config for this app",
    )
    slack_integration_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Slack config for this app",
    )
    discord_integration_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Discord config for this app",
    )
    twilio_integration_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Twilio config for this app",
    )

    @property
    def web_config(self):
        profile = Profile.objects.get(user=self.owner)
        return (
            WebIntegrationConfig().from_dict(
                self.web_integration_config,
                profile.decrypt_value,
            )
            if self.web_integration_config
            else None
        )

    @property
    def slack_config(self):
        profile = Profile.objects.get(user=self.owner)
        return (
            SlackIntegrationConfig().from_dict(
                self.slack_integration_config,
                profile.decrypt_value,
            )
            if self.slack_integration_config
            else None
        )

    @property
    def discord_config(self):
        profile = Profile.objects.get(user=self.owner)
        return (
            DiscordIntegrationConfig().from_dict(
                self.discord_integration_config,
                profile.decrypt_value,
            )
            if self.discord_integration_config
            else None
        )

    @property
    def twilio_config(self):
        profile = Profile.objects.get(user=self.owner)
        return (
            TwilioIntegrationConfig().from_dict(
                self.twilio_integration_config,
                profile.decrypt_value,
            )
            if self.twilio_integration_config
            else None
        )

    @discord_config.setter
    def discord_config(self, value):
        profile = Profile.objects.get(user=self.owner)
        self.discord_integration_config = (
            DiscordIntegrationConfig(
                **value,
            ).to_dict(profile.encrypt_value)
            if value
            else {}
        )

    def has_write_permission(self, user):
        if not user or not user.is_authenticated:
            return False

        return self.owner == user or (self.is_published and user.email in self.write_accessible_by)

    def has_read_permission(self, user):
        if not user or not user.is_authenticated:
            return False

        return self.owner == user or (self.is_published and user.email in self.read_accessible_by)

    def __str__(self) -> str:
        return self.name + " - " + self.owner.username


def create_image_asset_thumbnail_file(data_uri, dimensions=(300, 300), format="PNG"):
    from llmstack.common.utils.utils import generate_thumbnail, validate_parse_data_uri

    mimetype, filename, data = validate_parse_data_uri(data_uri)
    asset_image_bytes = base64.b64decode(data)
    return ContentFile(generate_thumbnail(asset_image_bytes, dimensions, format), name=f"public/apps/{filename}")


class AppData(models.Model):
    """
    Represents versioned app data
    """

    app_uuid = models.UUIDField(
        default=None,
        help_text="UUID of the app",
        null=True,
        blank=True,
    )
    version = models.IntegerField(
        default=0,
        help_text="Version of the app",
    )
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Data for this endpoint",
    )
    comment = models.TextField(
        default="",
        blank=True,
        help_text="Comment for this app version",
    )
    is_draft = models.BooleanField(
        default=True,
        help_text="Whether the data is draft or not",
    )
    is_dirty = models.BooleanField(
        default=False,
        help_text="Whether the data is dirty or not",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Time at which the app instance was created",
    )
    last_updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Time at which the app instance was last updated",
    )

    def __str__(self) -> str:
        return f'{self.app_uuid}_{"draft" if self.is_draft else "published"}_v{self.version}'

    def save(self, *args, **kwargs):
        if "config" in self.data:
            if "assistant_image" in self.data["config"]:
                if self.data["config"]["assistant_image"] and self.data["config"]["assistant_image"].startswith(
                    "data:image"
                ):
                    thumbnail_content_file = create_image_asset_thumbnail_file(
                        self.data["config"]["assistant_image"], (300, 300), "PNG"
                    )
                    stored_file_name = f"{thumbnail_content_file.name}_{str(uuid.uuid4())[:4]}_resized.png"
                    result = public_file_storage.save(stored_file_name, thumbnail_content_file)
                    url = public_file_storage.url(result)
                    self.data["config"]["assistant_image"] = url
        return super().save(*args, **kwargs)


def select_storage():
    from django.core.files.storage import storages

    return storages["assets"]


def appstore_upload_to(instance, filename):
    return "/".join(["appdata", str(instance.ref_id), filename])


class AppDataAssets(Assets):
    ref_id = models.UUIDField(help_text="Published UUID of the app this asset belongs to", null=False)
    file = models.FileField(
        storage=select_storage,
        upload_to=appstore_upload_to,
        null=True,
        blank=True,
    )

    def is_accessible(asset, request_user, request_session):
        app = App.objects.get(published_uuid=asset.ref_id)
        return app and (
            (app.is_published and app.is_public)
            or (app.has_read_permission(request_user) or app.has_write_permission(request_user))
        )


class AppHub(models.Model):
    app = models.ForeignKey(
        App,
        on_delete=models.DO_NOTHING,
        help_text="Public apps",
    )
    rank = models.IntegerField(default=0, help_text="Rank of the instance")
    categories = models.ManyToManyField(
        AppTemplateCategory,
        help_text="Categories of the app template",
        blank=True,
        default=None,
    )

    def __str__(self):
        return "{}_{}".format(self.app.name, self.app.published_uuid)

    def save(self, *args, **kwargs) -> None:
        # Make sure app is published and public before saving to app hub
        if self.app.is_published and self.app.is_public:
            return super().save(*args, **kwargs)
        else:
            raise Exception(
                "App should be published and public before saving to app hub",
            )


class AppSession(models.Model):
    """
    Instance of an app
    """

    uuid = models.UUIDField(default=uuid.uuid4, help_text="UUID for the run")
    app = models.ForeignKey(
        App,
        on_delete=models.DO_NOTHING,
        help_text="App of the app instance",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Time at which the app instance was created",
    )
    last_updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Time at which the app instance was last updated",
    )


class AppSessionData(models.Model):
    """
    Represents pickled backend processor data for an endpoint for a given session
    """

    app_session = models.ForeignKey(
        AppSession,
        on_delete=models.DO_NOTHING,
        help_text="App session",
    )
    endpoint = models.ForeignKey(
        Endpoint,
        on_delete=models.DO_NOTHING,
        help_text="Endpoint",
    )
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Data for this endpoint",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Time at which the app instance was created",
    )
    last_updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Time at which the app instance was last updated",
    )


def select_storage():
    from django.core.files.storage import storages

    return storages["assets"]


def appstore_upload_to(instance, filename):
    return "/".join(["app_sessions", str(instance.ref_id), filename])


class AppSessionFiles(Assets):
    ref_id = models.UUIDField(help_text="App session_id this file belongs to", blank=True, null=False)
    file = models.FileField(
        storage=select_storage,
        upload_to=appstore_upload_to,
        null=True,
        blank=True,
    )

    def is_accessible(asset, request_user, request_session):
        username = (
            request_user.username
            if request_user.is_authenticated
            else request_session["_prid"]
            if "_prid" in request_session
            else ""
        )
        metadata = asset.metadata

        # If the asset is public, anyone can access it
        if metadata.get("is_public", False):
            return True

        # If the asset is private, only the owner can access it
        if (
            metadata.get("owner", "")
            and request_user.is_authenticated
            and metadata.get("owner", "") == request_user.email
        ):
            return True

        if metadata.get("username", "") and metadata.get("username", "") == username:
            return True

        # If the asset is associated with an app, check if the user has access to the app
        app_uuid = metadata.get("app_uuid", "")
        if app_uuid:
            app = App.objects.get(uuid=app_uuid)
            if app.has_write_permission(request_user):
                return True

            # If username is unavailable in metadata and the app is public, user can access it
            if app.is_public and app.is_published and not metadata.get("username", "") and not username:
                return True

        return False


class TestSet(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        help_text="UUID for the test set",
    )
    name = models.CharField(
        max_length=100,
        help_text="Name of the app test set",
    )
    app = models.ForeignKey(
        App,
        on_delete=models.DO_NOTHING,
        help_text="App of the test set",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Time at which the app instance was created",
    )
    last_updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Time at which the app instance was last updated",
    )


class TestCase(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        help_text="UUID for the test case",
    )
    testset = models.ForeignKey(
        TestSet,
        on_delete=models.DO_NOTHING,
        help_text="Test set",
    )
    input_data = models.JSONField(
        default=dict,
        help_text="Test Case input data",
    )
    expected_output = models.TextField(
        default="",
        help_text="Expected output for the test case",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Time at which the app instance was created",
    )
    last_updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Time at which the app instance was last updated",
    )


@receiver(pre_save, sender=App)
def update_app_pre_save(sender, instance, **kwargs):
    from llmstack.apps.app_types import AppTypeFactory

    # Save discord and slack config
    discord_app_type_handler_cls = AppTypeFactory.get_app_type_handler(
        instance.type,
        "discord",
    )
    instance = discord_app_type_handler_cls.pre_save(instance)
    slack_app_type_handler_cls = AppTypeFactory.get_app_type_handler(
        instance.type,
        "slack",
    )
    instance = slack_app_type_handler_cls.pre_save(instance)

    twilio_sms_type_handler_cls = AppTypeFactory.get_app_type_handler(
        instance.type,
        "twilio_sms",
    )
    instance = twilio_sms_type_handler_cls.pre_save(instance)
