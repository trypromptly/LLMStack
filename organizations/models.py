import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.contrib.postgres.fields import ArrayField as PGArrayField
from django.db import connection
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from llmstack.common.utils.db_models import ArrayField

from llmstack.apps.models import AppVisibility


class Organization(models.Model):
    name = models.CharField(
        max_length=100, help_text='Name of the organization',
    )
    slug = models.SlugField(
        max_length=100, unique=True,
        help_text='Unique identifier for the organization', default=None, null=True, blank=True,
    )
    domains = PGArrayField(
        models.CharField(max_length=100), default=list, help_text='List of allowed domains of the organization',
    ) if connection.vendor == 'postgresql' else ArrayField(
        null=True, help_text='List of allowed domains of the organization',
    )
    admin_email = models.EmailField(
        max_length=100, help_text='Email of the admin of the organization',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    def is_admin(self, user):
        return self.admin_email == user.email

    def __str__(self):
        return self.name

    @property
    def settings(self):
        return OrganizationSettings.objects.get(organization=self)


class OrganizationSettings(models.Model):
    organization = models.OneToOneField(
        'Organization', on_delete=models.DO_NOTHING,
    )
    logo = models.ImageField(
        upload_to='organizations/logos/', default=None, null=True, blank=True,
    )
    disabled_api_backends = models.ManyToManyField(
        'apiabstractor.ApiBackend', blank=True, related_name='disabled_api_backends',
    )
    default_app_visibility = models.PositiveSmallIntegerField(
        default=AppVisibility.PUBLIC, choices=AppVisibility.choices, help_text='Default app visibility for the organization',
    )
    max_app_visibility = models.PositiveSmallIntegerField(
        default=AppVisibility.PUBLIC, choices=AppVisibility.choices, help_text='Maximum app visibility for the organization',
    )
    allow_user_keys = models.BooleanField(
        default=True, help_text='Whether to allow users to provide their own API keys or not',
    )
    # TODO: move API keys to a separate model since they are common between organization and user
    azure_openai_api_key = models.CharField(
        max_length=256, default=None, help_text='Azure OpenAI key to use with Azure backend', null=True, blank=True,
    )
    openai_key = models.CharField(
        max_length=256, default=None, help_text='OpenAI key to use with OpenAI backend', null=True, blank=True,
    )
    stabilityai_key = models.CharField(
        max_length=256, default=None, help_text='StabilityAI key to use with StabilityAI backend', null=True, blank=True,
    )
    cohere_key = models.CharField(
        max_length=256, default=None, help_text='Cohere API key to use with Cohere backend', null=True, blank=True,
    )
    forefrontai_key = models.CharField(
        max_length=256, default=None, help_text='ForefrontAI API key to use with ForefrontAI backend', null=True, blank=True,
    )
    elevenlabs_key = models.CharField(
        max_length=256, default=None, help_text='Elevenlabs API key to use with Elevenlabs backend', null=True, blank=True,
    )
    azure_openai_endpoint = models.CharField(
        max_length=256, default=None, help_text='Azure OpenAI endpoint to use with Azure openai processor', null=True, blank=True,
    )
    aws_access_key_id = models.CharField(
        max_length=256, default=None, help_text='AWS access key id to use with AWS backend', null=True, blank=True,
    )
    aws_secret_access_key = models.CharField(
        max_length=256, default=None, help_text='AWS access key secret to use with AWS backend', null=True, blank=True,
    )
    aws_default_region = models.CharField(
        max_length=64, default=None, help_text='AWS default region to use with AWS backend', null=True, blank=True,
    )
    localai_api_key = models.CharField(
        max_length=256, default=None, help_text='LocalAI API key to use with LocalAI backend', null=True, blank=True,
    )
    localai_base_url = models.CharField(
        max_length=256, default=None, help_text='LocalAI base URL to use with LocalAI backend', null=True, blank=True,
    )
    anthropic_api_key = models.CharField(
        max_length=256, default=None, help_text='Anthropic API key to use with Anthropic models like Claude', null=True, blank=True,
    )
    vectorstore_weaviate_url = models.CharField(
        max_length=256, default=None, help_text='Vectorstore URL to use with Vectorstore backend', null=True, blank=True,
    )
    vectorstore_weaviate_api_key = models.CharField(
        max_length=256, default=None, help_text='Vectorstore API key to use with Vectorstore backend', null=True, blank=True,
    )
    vectorstore_weaviate_text2vec_openai_module_config = models.JSONField(
        default=None, help_text='Text2Vec OpenAI module config to use with Vectorstore backend', null=True, blank=True,
    )
    use_own_vectorstore = models.BooleanField(
        default=False, help_text='Whether to use own Vectorstore instance or not',
    )
    use_azure_openai_embeddings = models.BooleanField(
        default=False, help_text='Whether to use Azure OpenAI embeddings or not',
    )
    embeddings_api_rate_limit = models.PositiveIntegerField(
        default=300, help_text='Rate limit for embeddings requests in requests/min',
    )
    embeddings_batch_size = models.PositiveIntegerField(
        default=20, help_text='Batch size for embeddings requests',
    )
    default_api_backend = models.ForeignKey(
        'apiabstractor.ApiBackend', on_delete=models.SET_NULL, null=True, blank=True, related_name='default_api_backend',
        help_text='Default API backend to use for the organization',
    )

    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.organization.name

    def get_vendor_key(self, attrname):
        if hasattr(self, attrname):
            encrypted_key = getattr(self, attrname)
            if encrypted_key and attrname in ['azure_openai_api_key', 'openai_key', 'stabilityai_key', 'cohere_key', 'forefrontai_key', 'elevenlabs_key', 'anthropic_api_key', 'aws_secret_access_key', 'vectorstore_weaviate_api_key']:
                return self.decrypt_value(encrypted_key)
            else:
                return encrypted_key
        return None

    def salt(self):
        salt_key = settings.CIPHER_KEY_SALT
        if not salt_key:
            raise Exception()
        return 'salt_{}'.format(salt_key).encode('utf-8')

    @staticmethod
    def get_cipher(token, salt):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256,
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
        cipher = OrganizationSettings.get_cipher(
            str(self.organization.slug), self.salt(),
        )
        return cipher.encrypt(value.encode()).decode('utf-8')

    def decrypt_value(self, value):
        if not value:
            return None
        cipher = OrganizationSettings.get_cipher(
            str(self.organization.slug), self.salt(),
        )
        return cipher.decrypt(value).decode()


@receiver(post_save, sender=Organization)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        OrganizationSettings.objects.create(organization=instance)
