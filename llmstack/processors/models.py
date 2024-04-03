import logging
import uuid

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField as PGArrayField
from django.db import connection, models
from django.db.models.signals import pre_save
from django.dispatch import receiver

from llmstack.common.utils.db_models import ArrayField

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


class Request(models.Model):
    """
    Model representing the request made against a versioned endpoint
    """

    from llmstack.apps.models import AppSession

    endpoint = models.ForeignKey(
        Endpoint,
        on_delete=models.DO_NOTHING,
        help_text="Version of endpoint this request made for",
    )
    param_values = models.JSONField(
        default=dict,
        help_text="Override param values with these",
    )
    prompt_values = models.JSONField(
        default=dict,
        help_text="Values for placeholders in the prompt",
    )
    input = models.JSONField(
        default=dict,
        help_text="Input to the API",
    )
    config = models.JSONField(
        default=dict,
        help_text="Configuration for this endpoint. Values for this will be set in endpoint when it is created",
        blank=True,
        null=True,
    )
    template_values = models.JSONField(
        default=dict,
        help_text="Values for placeholders in the input",
        blank=True,
        null=True,
    )
    created_on = models.DateTimeField(auto_now_add=True)
    app_session = models.ForeignKey(
        AppSession,
        on_delete=models.DO_NOTHING,
        help_text="App session this request was made for",
        null=True,
        blank=True,
        default=None,
    )
    app_session_key = models.CharField(
        max_length=100,
        help_text="App session this request was made for",
        null=True,
        blank=True,
        default=None,
    )
    app_id = models.IntegerField(
        default=None,
        null=True,
        blank=True,
        help_text="App this request was made for",
    )

    def __str__(self):
        return self.endpoint.name + ":" + str(self.endpoint.version)


class Response(models.Model):
    """
    Model that captures the repsonse from API backend as well as the response sent to the user
    """

    request = models.ForeignKey(
        Request,
        on_delete=models.DO_NOTHING,
        help_text="Request this response corresponds to",
    )
    raw_response = models.TextField(help_text="Raw response JSON from backend")
    processed_response = models.TextField(
        help_text="Output returned to the user after running the post processor",
    )
    response_code = models.IntegerField(
        help_text="Response code from the API backend",
    )
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.request.__str__()


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
    processor_runs = (
        PGArrayField(
            models.JSONField(
                default=dict,
                blank=True,
            ),
            default=list,
            help_text="Array of processor data for each endpoint including input and output data",
        )
        if connection.vendor == "postgresql"
        else ArrayField(
            null=True,
            help_text="Array of processor data for each endpoint including input and output data",
        )
    )
    platform_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Platform data for the run",
    )

    def __str__(self):
        return self.request_uuid

    @property
    def is_store_request(self):
        return self.app_store_uuid is not None

    @staticmethod
    def from_pinot_dict(row):
        owner = User.objects.get(id=row["owner_id"])

        return RunEntry(
            request_uuid=row["request_uuid"],
            app_uuid=row["app_uuid"],
            endpoint_uuid=row["endpoint_uuid"],
            owner=owner,
            session_key=row["session_key"],
            request_user_email=row["request_user_email"],
            request_ip=row["request_ip"],
            request_location=row["request_location"],
            request_user_agent=row["request_user_agent"],
            request_content_type=row["request_content_type"],
            request_body=row["request_body"],
            response_status=row["response_status"],
            response_body=row["response_body"],
            response_content_type=row["response_content_type"],
            response_headers=row["response_headers"],
            response_time=row["response_time"],
            processor_runs=row["processor_runs"],
        )


class EndpointInvocationCount(models.Model):
    """
    Model to track the usage of endpoints by users
    """

    user = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        help_text="User this count is for",
    )
    month = models.CharField(
        max_length=5,
        help_text="Month for the count as MM-YY",
        default="",
    )
    count = models.IntegerField(
        help_text="Count for the month",
        default=0,
    )

    def __str__(self):
        return self.user.__str__() + ":" + self.month


class Feedback(models.Model):
    """
    This is used to collect feedback about the response generated by backend. User can later collect these feedbacks and use them for finetuning
    """

    request = models.ForeignKey(
        Request,
        on_delete=models.DO_NOTHING,
        help_text="Request object this feedback is collected against",
    )
    response_quality = models.CharField(
        max_length=100,
        help_text="Quality rating for the response",
    )
    expected_response = models.CharField(
        max_length=100,
        help_text="Expected response for the response",
    )

    def __str__(self):
        return self.request.endpoint.name


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
    request = models.ForeignKey(
        Request,
        on_delete=models.DO_NOTHING,
        help_text="Request made for the test case",
    )
    response = models.ForeignKey(
        Response,
        on_delete=models.DO_NOTHING,
        help_text="Response for the test run",
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
