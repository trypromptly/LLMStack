import json
import logging
import uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver

from llmstack.assets.utils import get_asset_by_objref_internal

logger = logging.getLogger(__name__)


class ApiProvider(models.Model):
    """
    Collection of APIs belonging to the same provider
    """

    name = models.CharField(
        max_length=50,
        help_text="Name of the API backend (e.g., OpenAI V2",
    )
    slug = models.CharField(
        max_length=50,
        help_text="Slug for the API Provider",
        default="",
    )
    prefix = models.CharField(
        max_length=200,
        help_text="Prefix to use with all the outbound request URLs",
    )

    def __str__(self):
        return self.name


class ApiBackend(models.Model):
    """
    Actual API that we wrap over
    """

    name = models.CharField(max_length=50, help_text="Name of the API")
    slug = models.CharField(
        max_length=50,
        help_text="Slug for the API Backend",
        default="",
    )
    description = models.CharField(
        max_length=1000,
        help_text="Description of the API backend",
        blank=True,
        null=True,
        default="",
    )
    api_provider = models.ForeignKey(
        ApiProvider,
        on_delete=models.PROTECT,
        help_text="API Group this endpoint belongs to",
    )
    api_endpoint = models.CharField(
        max_length=100,
        help_text="URL endpoint used for this API",
    )
    params = models.JSONField(
        blank=True,
        help_text="A JSON containing name, type, default values, help text etc., for this API. For example, things like stop, echo",
        default=dict,
        null=True,
    )
    input_schema = models.JSONField(
        blank=True,
        help_text="Input fields for this backend in JSON schema format",
        default=dict,
        null=True,
    )
    output_schema = models.JSONField(
        blank=True,
        help_text="Output fields for this backend in JSON schema format",
        default=dict,
        null=True,
    )
    config_schema = models.JSONField(
        blank=True,
        help_text="Configuration for this backend. Values for this will be set in endpoint when it is created",
        default=dict,
        null=True,
    )

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ("api_provider", "name")


class Endpoint(models.Model):
    """
    User defined wrapper over the underlying API. User can override the default params for the API, define and test prompts
    """

    name = models.CharField(
        max_length=100,
        help_text="User provided name for an instance of API endpoint",
    )
    uuid = models.UUIDField(
        default=uuid.uuid4,
        help_text="Used to run APIs",
    )
    api_backend = models.ForeignKey(
        ApiBackend,
        on_delete=models.PROTECT,
        help_text="Backend endpoint this eventually calls",
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        help_text="Owner of this endpoint",
    )
    param_values = models.JSONField(
        default=dict,
        help_text="User provided param values that overrides the defaults used by the API",
    )
    post_processor = models.CharField(
        blank=True,
        max_length=100,
        help_text="A regular expression that can be run on the output",
    )
    draft = models.BooleanField(
        blank=True,
        default=False,
        help_text="We create draft endpoints when testing from playground",
    )
    prompt = models.TextField(
        default="",
        blank=False,
        help_text="Prompt used with this API. Use {{}} to provide variable placeholders in snake_case which will be replaced by prompt_values in tests and requests",
    )
    config = models.JSONField(
        default=dict,
        help_text="Configuration for this endpoint. Values for this will be set in endpoint when it is created",
        blank=True,
    )
    input = models.JSONField(
        default=dict,
        help_text="Input for this endpoint. Use {{}} to provide variable placeholders in snake_case which will be replaced by template_values in tests and requests",
        blank=True,
    )
    is_live = models.BooleanField(
        default=False,
        help_text="True for the version that is currently serving production traffic",
    )
    is_app = models.BooleanField(
        default=False,
        help_text="True for the version that is used by an app",
    )
    version = models.IntegerField(
        default=0,
        editable=False,
        help_text="Version number for the endpoint",
    )
    created_on = models.DateTimeField(auto_now_add=True)
    parent_uuid = models.UUIDField(
        default=None,
        blank=True,
        null=True,
        help_text="UUID of parent endpoint",
    )
    description = models.CharField(
        default="",
        max_length=100,
        help_text="Commit message for this version",
    )

    def __str__(self):
        return self.name + ":" + str(self.version)


class VersionedEndpoint(models.Model):
    """
    Versioned endpoint that maintains the prompts, enabling history of changes and ability to rollback
    """

    endpoint = models.ForeignKey(
        Endpoint,
        on_delete=models.PROTECT,
        help_text="Parent endpoint",
    )
    param_values = models.JSONField(
        blank=True,
        default=dict,
        help_text="Override param values",
    )
    prompt = models.TextField(
        blank=False,
        help_text="Prompt used with this API. Use {{}} to provide variable placeholders in snake_case which will be replaced by prompt_values in tests and requests",
    )
    post_processor = models.CharField(
        blank=True,
        max_length=100,
        help_text="A regular expression that can be run on the output. Overrides the one defined in the parent endpoint",
    )
    is_live = models.BooleanField(
        default=False,
        help_text="True for the version that is currently serving production traffic",
    )
    version = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        help_text="Version string for the endpoint",
    )
    created_on = models.DateTimeField(auto_now_add=True)
    description = models.CharField(
        max_length=100,
        help_text="Commit message for this version",
    )

    def __str__(self):
        return self.version.__str__()


class RunEntry(models.Model):
    """
    Represents a run of an app or an endpoint
    """

    request_uuid = models.CharField(
        max_length=40,
        default=uuid.uuid4,
        help_text="UUID for the run",
    )
    app_uuid = models.CharField(
        max_length=40,
        help_text="UUID of the app",
        default=None,
        null=True,
    )
    app_store_uuid = models.CharField(
        max_length=40,
        help_text="UUID of the app store",
        default=None,
        null=True,
    )
    endpoint_uuid = models.CharField(
        max_length=40,
        help_text="UUID of the endpoint",
        default=None,
        null=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Time at which the app instance was created",
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        help_text="Owner of the app or endpoint",
    )
    session_key = models.CharField(
        max_length=40,
        help_text="Session key",
        default=None,
        null=True,
    )
    request_user_email = models.CharField(
        max_length=320,
        help_text="User email",
        default=None,
        null=True,
    )
    request_ip = models.CharField(
        max_length=40,
        help_text="Request IP",
    )
    request_location = models.CharField(
        max_length=100,
        help_text="Request location",
    )
    request_user_agent = models.CharField(
        max_length=256,
        help_text="Request user agent",
    )
    request_content_type = models.CharField(
        max_length=100,
        help_text="Request Content-Type",
        default="application/json",
    )
    request_body = models.TextField(
        default="",
        blank=True,
        help_text="Request body",
    )
    response_status = models.IntegerField(
        default=0,
        help_text="Response status",
    )
    response_content_type = models.CharField(
        max_length=100,
        help_text="Response Content-Type",
        default="application/json",
    )
    response_body = models.TextField(
        default="",
        blank=True,
        help_text="Response body",
    )
    response_time = models.FloatField(
        default=0,
        help_text="Response time in seconds",
    )
    response_headers = models.JSONField(
        default=dict,
        blank=True,
        help_text="Response headers",
    )
    processor_runs_objref = models.CharField(
        default=None,
        blank=True,
        null=True,
        help_text="Processor runs objref",
    )
    platform_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Platform data for the run",
    )

    class Meta:
        indexes = [
            models.Index(fields=["request_uuid"]),
            models.Index(fields=["app_uuid"]),
            models.Index(fields=["app_store_uuid"]),
            models.Index(fields=["session_key"]),
        ]

    def __str__(self):
        return self.request_uuid

    def clean_dict(self, data):
        if isinstance(data, dict):
            return {key: self.clean_dict(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.clean_dict(element) for element in data]
        elif isinstance(data, str):
            return data.replace("\u0000", "")
        return data

    def clean_processor_runs(self, processor_runs=[]):
        return [self.clean_dict(item) for item in processor_runs]

    def save(self, *args, **kwargs):
        # Clean the processor_runs field
        processor_runs = kwargs.pop("processor_runs", [])
        processor_runs_objref = self.create_processor_runs_objref(processor_runs)
        self.processor_runs_objref = processor_runs_objref
        super(RunEntry, self).save(*args, **kwargs)

    @property
    def is_store_request(self):
        return self.app_store_uuid is not None

    def create_processor_runs_objref(self, processor_runs=[]):
        import base64
        import json

        from llmstack.apps.models import AppSessionFiles

        processor_runs = self.clean_processor_runs(processor_runs)
        processor_runs = {"processor_runs": processor_runs}

        request_uuid = str(self.request_uuid)
        processor_runs_datauri = f"data:application/json;name={request_uuid}_processor_runs.json;base64,{base64.b64encode(json.dumps(processor_runs).encode()).decode()}"

        session_id = self.session_key
        processor_runs_objrefs = AppSessionFiles.create_from_data_uri(
            data_uri=processor_runs_datauri,
            ref_id=session_id,
            metadata={"session_id": session_id, "request_uuid": request_uuid},
        )
        return processor_runs_objrefs.objref

    def get_processor_runs_from_objref(self):
        if not self.processor_runs_objref:
            return []
        file_asset = get_asset_by_objref_internal(self.processor_runs_objref)
        content = file_asset.file.read().decode("utf-8")
        return json.loads(content).get("processor_runs", [])

    @classmethod
    def get_processor_runs(cls, processor_runs_objref):
        if not processor_runs_objref:
            return []
        file_asset = get_asset_by_objref_internal(processor_runs_objref)
        content = file_asset.file.read().decode("utf-8")
        return json.loads(content).get("processor_runs", [])

    @property
    def feedback(self):
        return Feedback.objects.filter(request_uuid=self.request_uuid).first()


class Feedback(models.Model):
    """
    This is used to collect feedback about the response generated by backend. User can later collect these feedbacks and use them for finetuning
    """

    request_uuid = models.CharField(
        max_length=40, default=uuid.uuid4, help_text="Reference to run entry", null=False, unique=True
    )
    response_quality = models.SmallIntegerField(
        null=False,
        max_length=10,
        help_text="Quality rating for the response",
    )
    response_feedback = models.TextField(
        null=True,
        help_text="Expected response for the response",
    )


class TestSet(models.Model):
    """
    Set of test cases to run on the endpoint
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        help_text="Test Set Identifier",
    )
    endpoint = models.ForeignKey(
        Endpoint,
        on_delete=models.DO_NOTHING,
        help_text="Endpoint to run the test suite on",
    )
    param_values = models.JSONField(
        blank=True,
        default=dict,
        help_text="Override the params configured in the endpoint",
    )

    def __str__(self):
        return self.uuid.__str__()


class TestCase(models.Model):
    """
    Individual test case
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        help_text="Test Case Identifier",
    )
    testset = models.ForeignKey(
        TestSet,
        on_delete=models.DO_NOTHING,
        help_text="Test suite this test case is part of",
    )
    name = models.CharField(
        max_length=100,
        help_text="Short description for test",
    )
    prompt_values = models.JSONField(
        blank=True,
        help_text="Values for placeholders in the prompt",
    )
    expected_output = models.CharField(
        max_length=30,
        blank=True,
        help_text="Expected response for the given prompt values",
    )

    def __str__(self):
        return self.name


class TestRun(models.Model):
    """
    Test case run instance
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        help_text="Test Case Identifier",
    )
    testcase = models.ForeignKey(
        TestCase,
        on_delete=models.DO_NOTHING,
        help_text="Test case for the run",
    )
    endpoint = models.ForeignKey(
        Endpoint,
        null=True,
        on_delete=models.DO_NOTHING,
        help_text="Endpoint this is run against",
    )
    created_on = models.DateTimeField(auto_now_add=True)


class TestResult(models.Model):
    """
    Test case run result
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        help_text="Test Case Identifier",
    )
    testrun = models.ForeignKey(
        TestRun,
        on_delete=models.DO_NOTHING,
        help_text="Test run tied to the result",
    )


class TestSetRun(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        help_text="Identifier",
    )
    testset = models.ForeignKey(
        TestSet,
        on_delete=models.DO_NOTHING,
        help_text="Test Set for the run",
    )
    testruns = models.ManyToManyField(TestRun)
    created_on = models.DateTimeField(auto_now_add=True)


class ShareTag(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


@receiver(pre_save, sender=Endpoint)
def auto_increment_version(sender, instance, **kwrags):
    if instance.parent_uuid:
        latest = (
            Endpoint.objects.filter(
                parent_uuid=instance.parent_uuid,
            )
            .order_by("-version")
            .first()
        )
        if instance.uuid != instance.parent_uuid:
            # Copy endpoint name unless we are renaming version 0
            instance.name = getattr(latest, "name")
        instance.version = getattr(latest, "version") + 1
    else:
        instance.parent_uuid = instance.uuid
