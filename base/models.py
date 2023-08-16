from django.db import models
import base64
import json
import logging
import uuid

from enum import Enum
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from rest_framework.authtoken.models import Token
from django.utils.module_loading import import_string
from rest_framework.authtoken.models import Token

from emails.sender import EmailSender
from emails.templates.factory import EmailTemplateFactory

logger = logging.getLogger(__name__)


class VectorstoreEmbeddingEndpoint(Enum):
    OPEN_AI = 'openai'
    AZURE_OPEN_AI = 'azure_openai'


class AbstractProfile(models.Model):
    """
    Profile that attaches token to the user
    """
    class Meta:
        abstract = True

    user = models.OneToOneField(
        User, on_delete=models.DO_NOTHING, help_text='User this profile belongs to',
        related_name='user'
    )
    uuid = models.UUIDField(default=uuid.uuid4, help_text='User UUID')
    token = models.CharField(
        max_length=50,
        help_text='Token used to authenticate requests with',
    )
    organization = models.ForeignKey(
        'organizations.Organization', on_delete=models.DO_NOTHING, help_text='Organization this user belongs to', null=True, default=None, blank=True,
        related_name='organization'
    )
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
    google_service_account_json_key = models.TextField(
        default=None, help_text='Google service account key to use with Google backend', null=True, blank=True,
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
        max_length=256, default=None, help_text='LocalAI base URL to use with LocalAI processors', null=True, blank=True,
    )
    logo = models.TextField(
        default='', help_text='Logo to use for the user', null=True, blank=True,
    )

    def __str__(self):
        return self.user.__str__()

    @property
    def weaviate_url(self):
        if self.organization and self.organization.settings and self.organization.settings.vectorstore_weaviate_url:
            return self.organization.settings.vectorstore_weaviate_url
        return settings.WEAVIATE_URL

    @property
    def weaviate_api_key(self):
        if self.organization and self.organization.settings and self.organization.settings.vectorstore_weaviate_api_key:
            return self.organization.settings.decrypt_value(self.organization.settings.vectorstore_weaviate_api_key)

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
        if self.organization and self.organization.settings and self.organization.settings.use_own_vectorstore and self.organization.settings.vectorstore_weaviate_text2vec_openai_module_config:
            return json.loads(self.organization.settings.vectorstore_weaviate_text2vec_openai_module_config)

        return settings.WEAVIATE_TEXT2VEC_MODULE_CONFIG

    @property
    def vectorstore_embeddings_batch_size(self):
        if self.organization and self.organization.settings and self.organization.settings.embeddings_batch_size:
            return self.organization.settings.embeddings_batch_size

        return settings.WEAVIATE_EMBEDDINGS_BATCH_SIZE

    @property
    def use_custom_embedding(self):
        return settings.USE_CUSTOM_EMBEDDING

    def _vendor_key_or_promptly_default(self, attrname, api_key_value):
        if attrname == 'azure_openai_api_key':
            return self.decrypt_value(api_key_value) if api_key_value else settings.DEFAULT_AZURE_OPENAI_API_KEY
        elif attrname == 'openai_key':
            return self.decrypt_value(api_key_value) if api_key_value else settings.DEFAULT_OPENAI_API_KEY
        elif attrname == 'stabilityai_key':
            return self.decrypt_value(api_key_value) if api_key_value else settings.DEFAULT_DREAMSTUDIO_API_KEY
        elif attrname == 'cohere_key':
            return self.decrypt_value(api_key_value) if api_key_value else settings.DEFAULT_COHERE_API_KEY
        elif attrname == 'forefrontai_key':
            return self.decrypt_value(api_key_value) if api_key_value else settings.DEFAULT_FOREFRONTAI_API_KEY
        elif attrname == 'elevenlabs_key':
            return self.decrypt_value(api_key_value) if api_key_value else settings.DEFAULT_ELEVENLABS_API_KEY
        elif attrname == 'google_service_account_json_key':
            return self.decrypt_value(api_key_value) if api_key_value else settings.DEFAULT_GOOGLE_SERVICE_ACCOUNT_JSON_KEY
        elif attrname == 'aws_secret_access_key':
            return self.decrypt_value(api_key_value) if api_key_value else None
        elif attrname == 'aws_default_region':
            return self.decrypt_value(api_key_value) if api_key_value else None
        elif attrname == 'azure_openai_endpoint':
            return self.decrypt_value(api_key_value) if api_key_value else None
        elif attrname in ['aws_access_key_id']:
            return api_key_value
        elif attrname == 'localai_api_key':
            return self.decrypt_value(api_key_value) if api_key_value else None
        elif attrname == 'localai_base_url':
            return api_key_value
        else:
            return None

    def get_vendor_key(self, attrname):
        encrypted_key = None
        if hasattr(self, attrname):
            encrypted_key = getattr(self, attrname)

        if self.organization and self.organization.settings:
            # User belongs to an organization, check if the organization has a key
            org_key = self.organization.settings.get_vendor_key(attrname)
            if org_key:
                return org_key
            elif not org_key and self.organization.settings.allow_user_keys:
                return self._vendor_key_or_promptly_default(attrname, encrypted_key)
            else:
                return None
        else:
            # User does not belong to an organization, use user key
            return self._vendor_key_or_promptly_default(attrname, encrypted_key)

    def get_vendor_env(self):
        return {
            'azure_openai_api_key': self.get_vendor_key('azure_openai_api_key'),
            'openai_api_key': self.get_vendor_key('openai_key'),
            'stabilityai_api_key': self.get_vendor_key('stabilityai_key'),
            'cohere_api_key': self.get_vendor_key('cohere_key'),
            'forefrontai_api_key': self.get_vendor_key('forefrontai_key'),
            'elevenlabs_api_key': self.get_vendor_key('elevenlabs_key'),
            'google_service_account_json_key': self.get_vendor_key('google_service_account_json_key'),
            'aws_access_key_id': self.get_vendor_key('aws_access_key_id'),
            'aws_secret_access_key': self.get_vendor_key('aws_secret_access_key'),
            'aws_default_region': self.get_vendor_key('aws_default_region'),
            'azure_openai_endpoint': self.get_vendor_key('azure_openai_endpoint'),
            'localai_api_key': self.get_vendor_key('localai_key'),
            'localai_base_url': self.get_vendor_key('localai_base_url'),
            'weaviate_url': self.weaviate_url,
            'weaviate_api_key': self.weaviate_api_key,
            'weaviate_embedding_endpoint': self.vectostore_embedding_endpoint,
            'weaviate_text2vec_config': self.weaviate_text2vec_config,
        }

    def is_basic_subscriber(self):
        return False

    def is_pro_subscriber(self):
        return True

    def regenerate_token(self):
        t = Token.objects.get(user=self.user).delete()
        t = Token.objects.create(user=self.user)
        self.token = t.key
        self.save(update_fields=['token'])

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
        cipher = Profile.get_cipher(str(self.uuid), self.salt())
        return cipher.encrypt(value.encode())

    def decrypt_value(self, value):
        if not value:
            return None
        cipher = Profile.get_cipher(str(self.uuid), self.salt())
        return cipher.decrypt(value).decode()


class DefaultProfile(AbstractProfile):
    class Meta:
        app_label = 'base'
        db_table = 'base_profile'


def get_profile_model():
    # Look for a custom profile model in settings. If none is available, use the default.
    return import_string(getattr(settings, 'AUTH_PROFILE_CLASS', 'base.models.DefaultProfile'))


Profile = get_profile_model()


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        t = Token.objects.create(user=instance)
        # Check if there is an organization that has domains that match the email domain
        from organizations.models import Organization
        org = Organization.objects.filter(
            domains__contains=[instance.email.split('@')[1]],
        ).first() if instance.email else None
        Profile.objects.create(user=instance, token=t.key, organization=org)

        # Send welcome email
        if instance.email:
            email_template_cls = EmailTemplateFactory.get_template_by_name(
                'new_user_welcome',
            )
            email_sender = EmailSender(email_template_cls(user=instance))
            email_sender.send()
