import base64
import json
import logging
import uuid
from enum import Enum
from functools import cache

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils.module_loading import import_string
from rest_framework.authtoken.models import Token

from llmstack.common.utils.provider_config import validate_provider_configs
from llmstack.connections.models import Connection
from llmstack.emails.sender import EmailSender
from llmstack.emails.templates.factory import EmailTemplateFactory
from llmstack.processors.providers.promptly import SendgridEmailSenderConfig

logger = logging.getLogger(__name__)


@cache
def get_vendor_env_platform_defaults():
    from llmstack.processors.providers.anthropic import AnthropicProviderConfig
    from llmstack.processors.providers.azure import AzureProviderConfig
    from llmstack.processors.providers.cohere import CohereProviderConfig
    from llmstack.processors.providers.config import ProviderConfigSource
    from llmstack.processors.providers.elevenlabs import ElevenLabsProviderConfig
    from llmstack.processors.providers.google import GoogleProviderConfig
    from llmstack.processors.providers.meta import MetaProviderConfig
    from llmstack.processors.providers.mistral import MistralProviderConfig
    from llmstack.processors.providers.openai import OpenAIProviderConfig
    from llmstack.processors.providers.promptly import (
        DataDestinationConfig,
        EmbeddingsGeneratorConfig,
        GoogleSearchEngineConfig,
        PromptlyProviderConfig,
    )
    from llmstack.processors.providers.stabilityai import StabilityAIProviderConfig
    from llmstack.processors.providers.weaviate import (  # Populate the default provider configs
        EmbeddingsProvider,
        WeaviateLocalInstance,
        WeaviateProviderConfig,
    )

    provider_configs = {}
    promptly_provider_config = PromptlyProviderConfig()
    if settings.SENDGRID_API_KEY:
        sendgrid_email_sender_config = SendgridEmailSenderConfig(api_key=settings.SENDGRID_API_KEY)
        if settings.EMAIL_SENDER_FROM_ADDRESS:
            sendgrid_email_sender_config.from_email = settings.EMAIL_SENDER_FROM_ADDRESS
        promptly_provider_config.email_sender = sendgrid_email_sender_config
    if settings.DEFAULT_AZURE_OPENAI_API_KEY:
        provider_configs["azure/*/*/*"] = AzureProviderConfig(
            api_key=settings.DEFAULT_AZURE_OPENAI_API_KEY,
            provider_config_source=ProviderConfigSource.PLATFORM_DEFAULT.value,
        ).model_dump()
    if settings.DEFAULT_OPENAI_API_KEY:
        provider_configs["openai/*/*/*"] = OpenAIProviderConfig(
            api_key=settings.DEFAULT_OPENAI_API_KEY,
            provider_config_source=ProviderConfigSource.PLATFORM_DEFAULT.value,
        ).model_dump()
    if settings.DEFAULT_DREAMSTUDIO_API_KEY:
        provider_configs["stabilityai/*/*/*"] = StabilityAIProviderConfig(
            api_key=settings.DEFAULT_DREAMSTUDIO_API_KEY,
            provider_config_source=ProviderConfigSource.PLATFORM_DEFAULT.value,
        ).model_dump()
    if settings.DEFAULT_COHERE_API_KEY:
        provider_configs["cohere/*/*/*"] = CohereProviderConfig(
            api_key=settings.DEFAULT_COHERE_API_KEY,
            provider_config_source=ProviderConfigSource.PLATFORM_DEFAULT.value,
        ).model_dump()
    if settings.DEFAULT_ELEVENLABS_API_KEY:
        provider_configs["elevenlabs/*/*/*"] = ElevenLabsProviderConfig(
            api_key=settings.DEFAULT_ELEVENLABS_API_KEY,
            provider_config_source=ProviderConfigSource.PLATFORM_DEFAULT.value,
        ).model_dump()
    if settings.DEFAULT_GOOGLE_SERVICE_ACCOUNT_JSON_KEY:
        provider_configs["google/*/*/*"] = GoogleProviderConfig(
            service_account_json_key=settings.DEFAULT_GOOGLE_SERVICE_ACCOUNT_JSON_KEY,
            provider_config_source=ProviderConfigSource.PLATFORM_DEFAULT.value,
        ).model_dump()
    if settings.DEFAULT_MISTRAL_API_KEY:
        provider_configs["mistral/*/*/*"] = MistralProviderConfig(
            api_key=settings.DEFAULT_MISTRAL_API_KEY,
            provider_config_source=ProviderConfigSource.PLATFORM_DEFAULT.value,
        ).model_dump()
    if settings.DEFAULT_ANTHROPIC_API_KEY:
        provider_configs["anthropic/*/*/*"] = AnthropicProviderConfig(
            api_key=settings.DEFAULT_ANTHROPIC_API_KEY,
            provider_config_source=ProviderConfigSource.PLATFORM_DEFAULT.value,
        ).model_dump()
    if settings.DEFAULT_GOOGLE_CUSTOM_SEARCH_API_KEY:
        promptly_provider_config.search_engine = GoogleSearchEngineConfig(
            api_key=settings.DEFAULT_GOOGLE_CUSTOM_SEARCH_API_KEY,
            cx=settings.DEFAULT_GOOGLE_CUSTOM_SEARCH_CX,
        )
    if settings.DEFAULT_DATA_DESTINATION_CONFIG:
        promptly_provider_config.data_destination_configuration = DataDestinationConfig(
            **settings.DEFAULT_DATA_DESTINATION_CONFIG
        )
    if settings.DEFAULT_EMBEDDINGS_GENERATOR_CONFIG:
        promptly_provider_config.embeddings_generator = EmbeddingsGeneratorConfig(
            **settings.DEFAULT_EMBEDDINGS_GENERATOR_CONFIG
        )
    if settings.DEFAULT_META_PROVIDER_CONFIG and isinstance(settings.DEFAULT_META_PROVIDER_CONFIG, dict):
        # Iterate over the meta provider config and add the provider configs
        for k, v in settings.DEFAULT_META_PROVIDER_CONFIG.items():
            provider_configs[k] = MetaProviderConfig(
                deployment_config=v,
                provider_config_source=ProviderConfigSource.PLATFORM_DEFAULT.value,
            ).model_dump()

    if settings.WEAVIATE_PROVIDER_CONFIG:
        from llmstack.processors.providers.weaviate import APIKey

        auth = None
        if settings.WEAVIATE_API_KEY:
            auth = APIKey(api_key=settings.WEAVIATE_API_KEY)

        provider_configs["weaviate/*/*/*"] = WeaviateProviderConfig(
            provider_slug="weaviate",
            instance=WeaviateLocalInstance(**settings.WEAVIATE_PROVIDER_CONFIG),
            auth=auth,
            additional_headers=[],
            embeddings_provider=EmbeddingsProvider.OPENAI,
            module_config=(
                json.dumps({"text2vec-openai": settings.WEAVIATE_TEXT2VEC_MODULE_CONFIG})
                if settings.WEAVIATE_TEXT2VEC_MODULE_CONFIG
                else None
            ),
        ).model_dump()

    provider_configs["promptly/*/*/*"] = promptly_provider_config.model_dump()

    return {
        "azure_openai_api_key": settings.DEFAULT_AZURE_OPENAI_API_KEY,
        "openai_api_key": settings.DEFAULT_OPENAI_API_KEY,
        "stabilityai_api_key": settings.DEFAULT_DREAMSTUDIO_API_KEY,
        "cohere_api_key": settings.DEFAULT_COHERE_API_KEY,
        "forefrontai_api_key": settings.DEFAULT_FOREFRONTAI_API_KEY,
        "elevenlabs_api_key": settings.DEFAULT_ELEVENLABS_API_KEY,
        "google_service_account_json_key": settings.DEFAULT_GOOGLE_SERVICE_ACCOUNT_JSON_KEY,
        "aws_access_key_id": settings.DEFAULT_AWS_ACCESS_KEY_ID,
        "mistral_api_key": settings.DEFAULT_MISTRAL_API_KEY,
        "provider_configs": provider_configs,
    }


class VectorstoreEmbeddingEndpoint(Enum):
    OPEN_AI = "openai"
    AZURE_OPEN_AI = "azure_openai"


class AbstractProfile(models.Model):
    """
    Profile that attaches token to the user
    """

    class Meta:
        abstract = True

    user = models.OneToOneField(
        User,
        on_delete=models.DO_NOTHING,
        help_text="User this profile belongs to",
        related_name="user",
    )
    uuid = models.UUIDField(default=uuid.uuid4, help_text="User UUID", unique=True)
    token = models.CharField(
        max_length=50,
        help_text="Token used to authenticate requests with",
    )
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.DO_NOTHING,
        help_text="Organization this user belongs to",
        null=True,
        default=None,
        blank=True,
        related_name="organization",
    )
    azure_openai_api_key = models.CharField(
        max_length=256,
        default=None,
        help_text="Azure OpenAI key to use with Azure backend",
        null=True,
        blank=True,
    )
    openai_key = models.CharField(
        max_length=256,
        default=None,
        help_text="OpenAI key to use with OpenAI backend",
        null=True,
        blank=True,
    )
    stabilityai_key = models.CharField(
        max_length=256,
        default=None,
        help_text="StabilityAI key to use with StabilityAI backend",
        null=True,
        blank=True,
    )
    cohere_key = models.CharField(
        max_length=256,
        default=None,
        help_text="Cohere API key to use with Cohere backend",
        null=True,
        blank=True,
    )
    forefrontai_key = models.CharField(
        max_length=256,
        default=None,
        help_text="ForefrontAI API key to use with ForefrontAI backend",
        null=True,
        blank=True,
    )
    elevenlabs_key = models.CharField(
        max_length=256,
        default=None,
        help_text="Elevenlabs API key to use with Elevenlabs backend",
        null=True,
        blank=True,
    )
    google_service_account_json_key = models.TextField(
        default=None,
        help_text="Google service account key to use with Google backend",
        null=True,
        blank=True,
    )
    aws_access_key_id = models.CharField(
        max_length=256,
        default=None,
        help_text="AWS access key id to use with AWS backend",
        null=True,
        blank=True,
    )
    aws_secret_access_key = models.CharField(
        max_length=256,
        default=None,
        help_text="AWS access key secret to use with AWS backend",
        null=True,
        blank=True,
    )
    aws_default_region = models.CharField(
        max_length=64,
        default=None,
        help_text="AWS default region to use with AWS backend",
        null=True,
        blank=True,
    )
    localai_api_key = models.CharField(
        max_length=256,
        default=None,
        help_text="LocalAI API key to use with LocalAI backend",
        null=True,
        blank=True,
    )
    localai_base_url = models.CharField(
        max_length=256,
        default=None,
        help_text="LocalAI base URL to use with LocalAI processors",
        null=True,
        blank=True,
    )
    anthropic_api_key = models.CharField(
        max_length=256,
        default=None,
        help_text="Anthropic API key to use with Anthropic models like Claude",
        null=True,
        blank=True,
    )
    mistral_api_key = models.CharField(
        max_length=256,
        default=None,
        help_text="Mistral API key to use with Mistral backend",
        null=True,
        blank=True,
    )
    logo = models.TextField(
        default="",
        help_text="Logo to use for the user",
        null=True,
        blank=True,
    )
    _connections = models.JSONField(
        default=dict,
        help_text="Encrypted connections config to use with processors",
        null=True,
        blank=True,
    )
    _provider_configs = models.JSONField(
        default=dict, help_text="Encrypted providers config to use with processors", null=True, blank=True
    )

    def __str__(self):
        return self.user.__str__()

    @property
    def weaviate_url(self):
        if self.organization and self.organization.settings and self.organization.settings.vectorstore_weaviate_url:
            return self.organization.settings.vectorstore_weaviate_url

        if (
            settings.VECTOR_DATABASES.get("default")
            and settings.VECTOR_DATABASES.get(
                "default",
            ).get("ENGINE")
            == "weaviate"
        ):
            return settings.VECTOR_DATABASES.get("default").get("HOST")

        return settings.WEAVIATE_URL

    @property
    def weaviate_api_key(self):
        # If the user is part of an organization, use from organization
        # settings
        if self.organization and self.organization.settings and self.organization.settings.vectorstore_weaviate_api_key:
            return self.organization.settings.decrypt_value(
                self.organization.settings.vectorstore_weaviate_api_key,
            )

        # Get details from settings
        if (
            settings.VECTOR_DATABASES.get("default")
            and settings.VECTOR_DATABASES.get(
                "default",
            ).get("ENGINE")
            == "weaviate"
        ):
            return settings.VECTOR_DATABASES.get("default").get("API_KEY")

        return None

    @property
    def vectostore_embedding_endpoint(self):
        if self.organization and self.organization.settings and self.organization.settings.use_azure_openai_embeddings:
            return VectorstoreEmbeddingEndpoint.AZURE_OPEN_AI

        return VectorstoreEmbeddingEndpoint.OPEN_AI

    @property
    def weaviate_embeddings_api_rate_limit(self):
        if self.organization and self.organization.settings and self.organization.settings.embeddings_api_rate_limit:
            return self.organization.settings.embeddings_api_rate_limit

        return settings.WEAVIATE_EMBEDDINGS_API_RATE_LIMIT

    @property
    def weaviate_text2vec_config(self):
        if (
            self.organization
            and self.organization.settings
            and self.organization.settings.use_own_vectorstore
            and self.organization.settings.vectorstore_weaviate_text2vec_openai_module_config
        ):
            return json.loads(
                self.organization.settings.vectorstore_weaviate_text2vec_openai_module_config,
            )

        return settings.WEAVIATE_TEXT2VEC_MODULE_CONFIG

    @property
    def vectorstore_embeddings_batch_size(self):
        if self.organization and self.organization.settings and self.organization.settings.embeddings_batch_size:
            return self.organization.settings.embeddings_batch_size

        return settings.WEAVIATE_EMBEDDINGS_BATCH_SIZE

    @property
    def provider_configs(self):
        return (
            json.loads(
                self.decrypt_value(self._provider_configs),
            )
            if self._provider_configs
            else {}
        )

    @property
    def connections(self):
        return (
            {
                k: json.loads(
                    self.decrypt_value(v),
                )
                for k, v in self._connections.items()
            }
            if self._connections
            else {}
        )

    def get_connection(self, id):
        return (
            json.loads(
                self.decrypt_value(
                    self._connections.get(
                        id,
                    ),
                ),
            )
            if self._connections and self._connections.get(id)
            else None
        )

    def add_connection(self, connection):
        connection_id = (
            connection["id"]
            if "id" in connection
            else str(
                uuid.uuid4(),
            )
        )

        # Check if connection already exists and merge the configuration
        existing_connection = self.get_connection(connection_id)
        if existing_connection:
            existing_connection["configuration"] = {
                **existing_connection["configuration"],
                **connection["configuration"],
            }
            existing_connection["status"] = connection["status"]
            existing_connection["name"] = connection["name"]
            existing_connection["description"] = connection["description"]
            connection = existing_connection

        connection_json = Connection(**connection).model_dump_json()
        if not self._connections:
            self._connections = {}
        self._connections[connection_id] = self.encrypt_value(
            connection_json,
        ).decode("utf-8")
        self.save(update_fields=["_connections"])

    def delete_connection(self, id):
        if self._connections and id in self._connections:
            del self._connections[id]
            self.save(update_fields=["_connections"])

    def get_connection_by_type(self, connection_type_slug):
        return [
            json.loads(
                self.decrypt_value(v),
            )
            for v in self._connections.values()
            if json.loads(
                self.decrypt_value(v),
            )["connection_type_slug"]
            == connection_type_slug
        ]

    def update_provider_configs(self, provider_configs):
        if not self._provider_configs:
            self._provider_configs = {}

        # Validate the provider configs. Raises an exception if the configs are
        # invalid
        validate_provider_configs(provider_configs)

        # Once all the configs are validated, encrypt the data
        self._provider_configs = self.encrypt_value(json.dumps(provider_configs)).decode("utf-8")
        self.save(update_fields=["_provider_configs"])

    def _vendor_key_or_promptly_default(self, attrname, api_key_value):
        if attrname == "azure_openai_api_key":
            return (
                self.decrypt_value(
                    api_key_value,
                )
                if api_key_value
                else settings.DEFAULT_AZURE_OPENAI_API_KEY
            )
        elif attrname == "openai_key":
            return (
                self.decrypt_value(
                    api_key_value,
                )
                if api_key_value
                else settings.DEFAULT_OPENAI_API_KEY
            )
        elif attrname == "stabilityai_key":
            return (
                self.decrypt_value(
                    api_key_value,
                )
                if api_key_value
                else settings.DEFAULT_DREAMSTUDIO_API_KEY
            )
        elif attrname == "cohere_key":
            return (
                self.decrypt_value(
                    api_key_value,
                )
                if api_key_value
                else settings.DEFAULT_COHERE_API_KEY
            )
        elif attrname == "forefrontai_key":
            return (
                self.decrypt_value(
                    api_key_value,
                )
                if api_key_value
                else settings.DEFAULT_FOREFRONTAI_API_KEY
            )
        elif attrname == "elevenlabs_key":
            return (
                self.decrypt_value(
                    api_key_value,
                )
                if api_key_value
                else settings.DEFAULT_ELEVENLABS_API_KEY
            )
        elif attrname == "google_service_account_json_key":
            return (
                self.decrypt_value(
                    api_key_value,
                )
                if api_key_value
                else settings.DEFAULT_GOOGLE_SERVICE_ACCOUNT_JSON_KEY
            )
        elif attrname == "aws_secret_access_key":
            return (
                self.decrypt_value(
                    api_key_value,
                )
                if api_key_value
                else settings.DEFAULT_AWS_SECRET_ACCESS_KEY
            )
        elif attrname == "aws_default_region":
            return (
                self.decrypt_value(
                    api_key_value,
                )
                if api_key_value
                else settings.DEFAULT_AWS_DEFAULT_REGION
            )
        elif attrname == "azure_openai_endpoint":
            return (
                self.decrypt_value(
                    api_key_value,
                )
                if api_key_value
                else settings.DEFAULT_AZURE_OPENAI_ENDPOINT
            )
        elif attrname in ["aws_access_key_id"]:
            return api_key_value if api_key_value else settings.DEFAULT_AWS_ACCESS_KEY_ID
        elif attrname == "localai_api_key":
            return (
                self.decrypt_value(
                    api_key_value,
                )
                if api_key_value
                else settings.DEFAULT_LOCALAI_API_KEY
            )
        elif attrname == "localai_base_url":
            return api_key_value if api_key_value else settings.DEFAULT_LOCALAI_BASE_URL
        elif attrname == "anthropic_api_key":
            return (
                self.decrypt_value(
                    api_key_value,
                )
                if api_key_value
                else settings.DEFAULT_ANTHROPIC_API_KEY
            )
        elif attrname == "mistral_api_key":
            return (
                self.decrypt_value(
                    api_key_value,
                )
                if api_key_value
                else settings.DEFAULT_MISTRAL_API_KEY
            )
        elif attrname == "google_custom_search_api_key":
            return api_key_value if api_key_value else settings.DEFAULT_GOOGLE_CUSTOM_SEARCH_API_KEY
        elif attrname == "google_custom_search_cx":
            return api_key_value if api_key_value else settings.DEFAULT_GOOGLE_CUSTOM_SEARCH_CX
        else:
            return None

    def get_vendor_key(self, attrname):
        encrypted_key = None
        if hasattr(self, attrname):
            encrypted_key = getattr(self, attrname)

        if self.organization and self.organization.settings:
            # User belongs to an organization, check if the organization has a
            # key
            org_key = self.organization.settings.get_vendor_key(attrname)
            if org_key:
                return org_key
            elif not org_key and self.organization.settings.allow_user_keys:
                return self._vendor_key_or_promptly_default(
                    attrname,
                    encrypted_key,
                )
            else:
                return None
        else:
            # User does not belong to an organization, use user key
            return self._vendor_key_or_promptly_default(
                attrname,
                encrypted_key,
            )

    def get_merged_provider_configs(self):
        from llmstack.processors.providers.config import ProviderConfigSource

        provider_configs = self.provider_configs
        if self.organization and self.organization.settings:
            org_provider_configs = self.organization.settings.provider_configs
            for k, v in org_provider_configs.items():
                if k not in provider_configs:
                    provider_configs[k] = {**v, **{"provider_config_source": ProviderConfigSource.ORGANIZATION.value}}

        # Add platform defaults
        platform_defaults = get_vendor_env_platform_defaults()
        for k, v in platform_defaults.get("provider_configs", {}).items():
            if k not in provider_configs:
                provider_configs[k] = v

        return provider_configs

    def get_vendor_env(self):
        return {
            "azure_openai_api_key": self.get_vendor_key("azure_openai_api_key"),
            "openai_api_key": self.get_vendor_key("openai_key"),
            "stabilityai_api_key": self.get_vendor_key("stabilityai_key"),
            "cohere_api_key": self.get_vendor_key("cohere_key"),
            "forefrontai_api_key": self.get_vendor_key("forefrontai_key"),
            "elevenlabs_api_key": self.get_vendor_key("elevenlabs_key"),
            "google_service_account_json_key": self.get_vendor_key("google_service_account_json_key"),
            "aws_access_key_id": self.get_vendor_key("aws_access_key_id"),
            "aws_secret_access_key": self.get_vendor_key("aws_secret_access_key"),
            "aws_default_region": self.get_vendor_key("aws_default_region"),
            "azure_openai_endpoint": self.get_vendor_key("azure_openai_endpoint"),
            "localai_api_key": self.get_vendor_key("localai_api_key"),
            "localai_base_url": self.get_vendor_key("localai_base_url"),
            "anthropic_api_key": self.get_vendor_key("anthropic_api_key"),
            "mistral_api_key": self.get_vendor_key("mistral_api_key"),
            "weaviate_url": self.weaviate_url,
            "weaviate_api_key": self.weaviate_api_key,
            "weaviate_embedding_endpoint": self.vectostore_embedding_endpoint,
            "weaviate_text2vec_config": self.weaviate_text2vec_config,
            "promptly_token": self.token,
            "connections": self.connections,
            "provider_configs": self.get_merged_provider_configs(),
            "google_custom_search_api_key": self.get_vendor_key("google_custom_search_api_key"),
            "google_custom_search_cx": self.get_vendor_key("google_custom_search_cx"),
        }

    def get_provider_config(
        self, model_slug: str = "*", deployment_key: str = "*", provider_slug=None, processor_slug=None
    ):
        from llmstack.common.utils.provider_config import get_matched_provider_config

        return get_matched_provider_config(
            provider_configs=self.get_vendor_env().get("provider_configs", {}),
            provider_slug=provider_slug,
            processor_slug=processor_slug,
            model_slug=model_slug,
            deployment_key=deployment_key,
        )

    def is_basic_subscriber(self):
        return False

    def is_pro_subscriber(self):
        return True

    def regenerate_token(self):
        t = Token.objects.get(user=self.user).delete()
        t = Token.objects.create(user=self.user)
        self.token = t.key
        self.save(update_fields=["token"])

    def salt(self):
        salt_key = settings.CIPHER_KEY_SALT
        if not salt_key:
            raise Exception()
        return "salt_{}".format(salt_key).encode("utf-8")

    @staticmethod
    def get_cipher(token, salt):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            iterations=100000,
            length=32,
            salt=salt,
            backend=default_backend(),
        )
        key = base64.urlsafe_b64encode(kdf.derive(token.encode()))
        cipher = Fernet(key)
        return cipher

    def encrypt_value(self, value):
        if not value:
            return None
        cipher = Profile.get_cipher(str(self.uuid), self.salt())
        return cipher.encrypt(value.encode())

    def decrypt_value(self, value):
        if not value:
            return None
        cipher = Profile.get_cipher(str(self.uuid), self.salt())
        return cipher.decrypt(value).decode()

    @property
    def encrypted_uuid(self):
        salt_key = settings.CIPHER_KEY_SALT.encode("utf-8")
        cipher = Profile.get_cipher("", salt_key)
        return cipher.encrypt(str(self.uuid).encode()).decode()

    @classmethod
    def get_by_encrypted_uuid(cls, encrypted_uuid):
        salt_key = settings.CIPHER_KEY_SALT.encode("utf-8")
        cipher = Profile.get_cipher("", salt_key)
        uuid = cipher.decrypt(encrypted_uuid.encode()).decode()
        return cls.objects.get(uuid=uuid)


class DefaultProfile(AbstractProfile):
    class Meta:
        app_label = "base"
        db_table = "base_profile"


def get_profile_model():
    # Look for a custom profile model in settings. If none is available, use
    # the default.
    return import_string(
        getattr(
            settings,
            "AUTH_PROFILE_CLASS",
            "llmstack.base.models.DefaultProfile",
        ),
    )


Profile = get_profile_model()


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        t = Token.objects.create(user=instance)
        # Check if there is an organization that has domains that match the
        # email domain
        from llmstack.organizations.models import Organization

        org = (
            Organization.objects.filter(
                domains__contains=[instance.email.split("@")[1]],
            ).first()
            if instance.email
            else None
        )
        Profile.objects.create(user=instance, token=t.key, organization=org)

        # Send welcome email
        if instance.email:
            email_template_cls = EmailTemplateFactory.get_template_by_name(
                "new_user_welcome",
            )
            email_sender = EmailSender(email_template_cls(user=instance))
            email_sender.send()


class AnonymousProfile:
    user = None
    uuid = None
    token = None
    organization = None
    azure_openai_api_key = None
    openai_key = None
    stabilityai_key = None
    cohere_key = None
    forefrontai_key = None
    elevenlabs_key = None
    google_service_account_json_key = None
    aws_access_key_id = None
    aws_secret_access_key = None
    aws_default_region = None
    localai_api_key = None
    localai_base_url = None
    anthropic_api_key = None
    mistral_api_key = None
    logo = None
    _connections = None
    _provider_configs = None

    def get_vendor_env(self):
        return get_vendor_env_platform_defaults()

    def is_basic_subscriber(self):
        return False

    def is_pro_subscriber(self):
        return False
