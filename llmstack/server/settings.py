import base64
import json
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-o25+*nb2h8_f6t7_^r7r1e#_p@0b)0(i@-wr(h1@!enw^co2&m",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False") == "True"

LLMSTACK_PORT = os.getenv("LLMSTACK_PORT", 3000)
LLMSTACK_HOST = os.getenv("LLMSTACK_HOST", "localhost")

ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS",
    f"127.0.0.1,localhost,{LLMSTACK_HOST}",
).split(",")


RUNNER_HOST = os.getenv("RUNNER_HOST", "runner")
RUNNER_PORT = os.getenv("RUNNER_PORT", 50051)
RUNNER_PLAYWRIGHT_PORT = os.getenv("RUNNER_PLAYWRIGHT_PORT", 50053)
PLAYWRIGHT_URL = f"ws://{RUNNER_HOST}:{RUNNER_PLAYWRIGHT_PORT}" if RUNNER_HOST and RUNNER_PLAYWRIGHT_PORT else ""

CSRF_TRUSTED_ORIGINS = os.getenv(
    "CSRF_TRUSTED_ORIGINS",
    f"http://{LLMSTACK_HOST}:{LLMSTACK_PORT}",
).split(",")

STATIC_ROOT = os.path.join(BASE_DIR, "static")

CIPHER_KEY_SALT = os.getenv("CIPHER_KEY_SALT", None)

ADMIN_ENABLED = os.getenv("ADMIN_ENABLED", True)

DATA_UPLOAD_MAX_MEMORY_SIZE = os.getenv(
    "DATA_UPLOAD_MAX_MEMORY_SIZE",
    26214400,
)  # 25MB default

# Application definition

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.sites",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "llmstack.processors.apps.ProcessorsConfig",
    "llmstack.data.apps.DatasourcesConfig",
    "llmstack.apps.apps.AppsConfig",
    "llmstack.app_store.apps.AppStoreConfig",
    "llmstack.base.apps.BaseConfig",
    "llmstack.connections.apps.ConnectionsConfig",
    "llmstack.jobs.apps.JobsConfig",
    "llmstack.organizations.apps.OrganizationsConfig",
    "llmstack.assets.apps.AssetsConfig",
    "llmstack.sheets.apps.SheetsConfig",
    "flags",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "django_rq",
    "django_jsonform",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "llmstack.apps.authorization_middleware.AuthorizationMiddleware",
]

ROOT_URLCONF = "llmstack.server.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "llmstack.server.wsgi.application"
ASGI_APPLICATION = "llmstack.server.asgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.{}".format(
            os.getenv("DATABASE_ENGINE", "postgresql"),
        ),
        "NAME": os.getenv(
            "DATABASE_NAME",
            "llmstack",
        ),
        "USER": os.getenv("DATABASE_USERNAME", "llmstack"),
        "PASSWORD": os.getenv("DATABASE_PASSWORD", "llmstack"),
        "HOST": os.getenv("DATABASE_HOST", "postgres"),
        "PORT": os.getenv("DATABASE_PORT", 5432),
    },
}

VECTOR_DATABASES = {
    "default": {
        "ENGINE": "{}".format(
            os.getenv("VECTOR_DATABASE_ENGINE", "weaviate"),
        ),
        "NAME": os.getenv("VECTOR_DATABASE_NAME", "llmstack"),
        "HOST": os.getenv("VECTOR_DATABASE_HOST", "http://weaviate:8080"),
        "USER": os.getenv("VECTOR_DATABASE_USERNAME", None),
        "PASSWORD": os.getenv("VECTOR_DATABASE_PASSWORD", None),
        "AUTH_TOKEN": os.getenv("VECTOR_DATABASE_AUTH_TOKEN", None),
        "API_KEY": os.getenv("VECTOR_DATABASE_API_KEY", None),
        "CONNECT_TIMEOUT": os.getenv("VECTOR_DATABASE_CONNECT_TIMEOUT", 5),
        "READ_TIMEOUT": os.getenv("VECTOR_DATABASE_READ_TIMEOUT", 60),
    },
}

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
]

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

REACT_APP_DIR = os.path.join(BASE_DIR, "client")
STATIC_URL = os.getenv("STATIC_URL", "static/")
STATICFILES_DIRS = [
    os.path.join(REACT_APP_DIR, "build", "static"),
]
GENERATEDFILES_ROOT = os.getenv(
    "GENERATEDFILES_ROOT",
    os.path.join(BASE_DIR, "generatedfiles"),
)
GENERATEDFILES_URL = os.getenv(
    "GENERATEDFILES_URL",
    "/generatedfiles/",
)
ASSETS_ROOT = os.getenv(
    "ASSETS_ROOT",
    "/home/appuser/data/assets",
)
ASSETS_URL = os.getenv(
    "ASSETS_URL",
    "/media/assets/",
)
PUBLIC_ASSETS_ROOT = os.getenv(
    "PUBLIC_ASSETS_ROOT",
    "/home/appuser/data/public_assets",
)
PUBLIC_ASSETS_URL = os.getenv(
    "PUBLIC_ASSETS_URL",
    "/media/public_assets/",
)

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
    "generatedfiles": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "location": GENERATEDFILES_ROOT,
            "base_url": GENERATEDFILES_URL,
        },
    },
    "assets": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "location": ASSETS_ROOT,
            "base_url": ASSETS_URL,
        },
    },
    "public_assets": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "location": PUBLIC_ASSETS_ROOT,
            "base_url": PUBLIC_ASSETS_URL,
        },
    },
}

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", os.getenv("LOG_LEVEL", "ERROR")),
        },
        "rq.worker": {
            "handlers": ["console"],
            "level": os.getenv("RQ_LOG_LEVEL", os.getenv("LOG_LEVEL", "ERROR")),
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("LOG_LEVEL", "ERROR"),
    },
}

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "llmstack.base.renderers.renderers.ORJSONRenderer",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

CACHES = {
    "default": {
        "BACKEND": f"django.core.cache.backends.{os.getenv('CACHE_BACKEND', 'redis.RedisCache')}",
        "LOCATION": f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}/1",
        "TIMEOUT": 3600,
    },
    "app_session": {
        "BACKEND": f"django.core.cache.backends.{os.getenv('CACHE_BACKEND', 'redis.RedisCache')}",
        "LOCATION": f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}/2",
        "TIMEOUT": 3600,
    },
    "app_session_data": {
        "BACKEND": f"django.core.cache.backends.{os.getenv('CACHE_BACKEND', 'redis.RedisCache')}",
        "LOCATION": f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}/3",
        "TIMEOUT": 3600,
    },
    "objref_stream": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}/4",
        "TIMEOUT": 3600,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}/5"],
        },
    },
}

APP_SESSION_TIMEOUT = int(os.getenv("APP_SESSION_TIMEOUT", 3600))

ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"
SITE_ID = 1
LOGIN_REDIRECT_URL = "/"
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_PROVIDERS = {}
ACCOUNT_ADAPTER = "llmstack.server.adapters.CustomAccountAdapter"
SOCIALACCOUNT_ADAPTER = "llmstack.server.adapters.CustomSocialAccountAdapter"

DEFAULT_AWS_SECRET_ACCESS_KEY = os.getenv("DEFAULT_AWS_SECRET_ACCESS_KEY", "")
DEFAULT_AWS_DEFAULT_REGION = os.getenv("DEFAULT_AWS_DEFAULT_REGION", "")
DEFAULT_AWS_ACCESS_KEY_ID = os.getenv("DEFAULT_AWS_ACCESS_KEY_ID", "")
DEFAULT_AZURE_OPENAI_API_KEY = os.getenv("DEFAULT_AZURE_OPENAI_API_KEY", "")
DEFAULT_AZURE_OPENAI_ENDPOINT = os.getenv("DEFAULT_AZURE_OPENAI_ENDPOINT", "")
DEFAULT_OPENAI_API_KEY = os.getenv("DEFAULT_OPENAI_API_KEY", "")
DEFAULT_DREAMSTUDIO_API_KEY = os.getenv("DEFAULT_DREAMSTUDIO_API_KEY", "")
DEFAULT_COHERE_API_KEY = os.getenv("DEFAULT_COHERE_API_KEY", "")
DEFAULT_FOREFRONTAI_API_KEY = os.getenv("DEFAULT_FOREFRONTAI_API_KEY", "")
DEFAULT_ELEVENLABS_API_KEY = os.getenv("DEFAULT_ELEVENLABS_API_KEY", "")
DEFAULT_ANTHROPIC_API_KEY = os.getenv("DEFAULT_ANTHRIPOC_API_KEY", "")
DEFAULT_MISTRAL_API_KEY = os.getenv("DEFAULT_MISTRAL_API_KEY", "")
DEFAULT_GOOGLE_SERVICE_ACCOUNT_JSON_KEY = os.getenv(
    "DEFAULT_GOOGLE_SERVICE_ACCOUNT_JSON_KEY",
    "{}",
)
DEFAULT_LOCALAI_API_KEY = os.getenv("DEFAULT_LOCALAI_API_KEY", "")
DEFAULT_LOCALAI_BASE_URL = os.getenv("DEFAULT_LOCALAI_BASE_URL", "")
DEFAULT_GOOGLE_CUSTOM_SEARCH_API_KEY = os.getenv(
    "DEFAULT_GOOGLE_CUSTOM_SEARCH_API_KEY",
    "",
)
DEFAULT_GOOGLE_CUSTOM_SEARCH_CX = os.getenv(
    "DEFAULT_GOOGLE_CUSTOM_SEARCH_CX",
    "",
)
DEFAULT_META_PROVIDER_CONFIG = {}
try:
    DEFAULT_META_PROVIDER_CONFIG = (
        json.loads(base64.b64decode(os.getenv("DEFAULT_META_PROVIDER_CONFIG")))
        if os.getenv("DEFAULT_META_PROVIDER_CONFIG")
        else {}
    )
except Exception:
    print("Error parsing DEFAULT_META_PROVIDER_CONFIG")

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
WEAVIATE_TEXT2VEC_MODULE_CONFIG = {
    "model": "ada",
    "type": "text",
}
WEAVIATE_EMBEDDINGS_API_RATE_LIMIT = 1000
WEAVIATE_EMBEDDINGS_BATCH_SIZE = 50
WEAVIATE_REPLICATION_FACTOR = int(
    os.getenv("WEAVIATE_REPLICATION_FACTOR", "1"),
)
WEAVIATE_SHARD_COUNT = int(os.getenv("WEAVIATE_SHARD_COUNT", "1"))

WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", os.getenv("VECTOR_DATABASE_API_KEY", None))

RQ_QUEUES = {
    "default": {
        "HOST": os.getenv(
            "REDIS_HOST",
            os.getenv(
                "RUNNER_RQ_REDIS_HOST",
                "localhost",
            ),
        ),
        "PORT": os.getenv(
            "REDIS_PORT",
            os.getenv(
                "RUNNER_RQ_REDIS_PORT",
                6379,
            ),
        ),
        "DB": os.getenv(
            "REDIS_DB",
            0,
        ),
        "DEFAULT_TIMEOUT": 1500,
    },
}

USE_REMOTE_JOB_QUEUE = os.getenv("USE_REMOTE_JOB_QUEUE", "True") == "True"
# Interval between two subtask runs in seconds
TASK_RUN_DELAY = int(os.getenv("TASK_RUN_DELAY", "60"))
# Maximum number of subtasks per task/job
MAX_SUBTASKS_PER_TASK = int(os.getenv("MAX_SUBTASKS_PER_TASK", "500"))

X_FRAME_OPTIONS = "SAMEORIGIN"

SITENAME = os.getenv("SITENAME", "Promptly")
SITE_URL = os.getenv("SITE_URL", "https://trypromptly.com")

INDEX_VIEW_MODULE = "llmstack.base.views"
EMAIL_SENDER_CLASS = "llmstack.emails.sender.DefaultEmailSender"
EMAIL_SENDER_FROM_ADDRESS = os.getenv("EMAIL_SENDER_FROM_ADDRESS", "")
EMAIL_TEMPLATE_FACTORY_CLASS = "llmstack.emails.templates.factory.DefaultEmailTemplateFactory"
FLAG_SOURCES = ["llmstack.base.flags.FlagSource"]

# Make sure name and slug are unique
PROVIDERS = [
    {
        "name": "Amazon",
        "datasource_packages": ["llmstack.data.sources.amazon"],
        "processor_exclude": [],
        "datasource_processors_exclude": [],
        "slug": "amazon",
    },
    {
        "name": "Anthropic",
        "processor_packages": ["llmstack.processors.providers.anthropic"],
        "processor_exclude": [],
        "datasource_processors_exclude": [],
        "slug": "anthropic",
        "config_schema": "llmstack.processors.providers.anthropic.AnthropicProviderConfig",
    },
    {
        "name": "Azure",
        "processor_packages": ["llmstack.processors.providers.azure"],
        "processor_exclude": [],
        "datasource_processors_exclude": [],
        "slug": "azure",
        "config_schema": "llmstack.processors.providers.azure.AzureProviderConfig",
    },
    {
        "name": "Cohere",
        "processor_packages": ["llmstack.processors.providers.cohere"],
        "processor_exclude": [],
        "datasource_processors_exclude": [],
        "slug": "cohere",
        "config_schema": "llmstack.processors.providers.cohere.CohereProviderConfig",
    },
    {
        "name": "ElevenLabs",
        "processor_packages": ["llmstack.processors.providers.elevenlabs"],
        "processor_exclude": [],
        "datasource_processors_exclude": [],
        "slug": "elevenlabs",
        "config_schema": "llmstack.processors.providers.elevenlabs.ElevenLabsProviderConfig",
    },
    {
        "name": "Google",
        "processor_packages": ["llmstack.processors.providers.google"],
        "slug": "google",
        "datasource_packages": ["llmstack.data.sources.google"],
        "processor_exclude": [],
        "datasource_processors_exclude": [],
        "config_schema": "llmstack.processors.providers.google.GoogleProviderConfig",
    },
    {
        "name": "Open AI",
        "processor_packages": ["llmstack.processors.providers.openai"],
        "processor_exclude": [],
        "datasource_processors_exclude": [],
        "slug": "openai",
        "config_schema": "llmstack.processors.providers.openai.OpenAIProviderConfig",
    },
    {
        "name": "Promptly",
        "processor_packages": ["llmstack.processors.providers.promptly"],
        "datasource_packages": [
            "llmstack.data.sources.databases",
            "llmstack.data.sources.files",
            "llmstack.data.sources.text",
            "llmstack.data.sources.website",
        ],
        "processor_exclude": [
            "llmstack.processors.providers.promptly.code_interpreter.CodeInterpreterProcessor",
        ],
        "datasource_processors_exclude": [],
        "slug": "promptly",
        "config_schema": "llmstack.processors.providers.promptly.PromptlyProviderConfig",
    },
    {
        "name": "Stability AI",
        "processor_packages": ["llmstack.processors.providers.stabilityai"],
        "processor_exclude": [],
        "datasource_processors_exclude": [],
        "slug": "stabilityai",
        "config_schema": "llmstack.processors.providers.stabilityai.StabilityAIProviderConfig",
    },
    {
        "name": "LinkedIn",
        "processor_packages": ["llmstack.processors.providers.linkedin"],
        "slug": "linkedin",
    },
    {
        "name": "Apollo",
        "processor_packages": ["llmstack.processors.providers.apollo"],
        "slug": "apollo",
    },
    {
        "name": "HeyGen",
        "processor_packages": ["llmstack.processors.providers.heygen"],
        "slug": "heygen",
    },
    {
        "name": "Mistral",
        "processor_packages": ["llmstack.processors.providers.mistral"],
        "slug": "mistral",
        "config_schema": "llmstack.processors.providers.mistral.MistralProviderConfig",
    },
    {
        "name": "Meta",
        "processor_packages": ["llmstack.processors.providers.meta"],
        "slug": "meta",
        "config_schema": "llmstack.processors.providers.meta.MetaProviderConfig",
    },
    {
        "name": "Pinecone",
        "slug": "pinecone",
        "config_schema": "llmstack.processors.providers.pinecone.PineconeProviderConfig",
    },
    {
        "name": "Qdrant",
        "slug": "qdrant",
        "config_schema": "llmstack.processors.providers.qdrant.QdrantProviderConfig",
    },
    {
        "name": "Singlestore",
        "slug": "singlestore",
        "config_schema": "llmstack.processors.providers.singlestore.SinglestoreProviderConfig",
    },
    {
        "name": "Weaviate",
        "slug": "weaviate",
        "config_schema": "llmstack.processors.providers.weaviate.WeaviateProviderConfig",
    },
]

WEAVIATE_PROVIDER_CONFIG = {
    "url": os.getenv("WEAVIATE_URL", "http://weaviate:8080"),
    "http_host": os.getenv("WEAVIATE_HTTP_HOST", "weaviate"),
    "http_port": os.getenv("WEAVIATE_HTTP_PORT", 8080),
    "http_secure": os.getenv("WEAVIATE_HTTP_SECURE", False),
    "grpc_host": os.getenv("WEAVIATE_GRPC_HOST", "weaviate"),
    "grpc_port": os.getenv("WEAVIATE_GRPC_PORT", 50051),
    "grpc_secure": os.getenv("WEAVIATE_GRPC_SECURE", False),
}

# Include networking providers if they are enabled
try:
    import jnpr.junos  # noqa: F401

    PROVIDERS.append(
        {
            "name": "Juniper",
            "processor_packages": ["llmstack.processors.providers.juniper"],
            "slug": "juniper",
        },
    )
except ImportError:
    pass

PROCESSOR_PROVIDERS = sum(
    list(
        map(
            lambda entry: entry["processor_packages"],
            filter(
                lambda provider: "processor_packages" in provider,
                PROVIDERS,
            ),
        ),
    ),
    [],
)

PROCESSOR_EXCLUDE_LIST = sum(
    list(
        map(
            lambda entry: entry["processor_exclude"],
            filter(
                lambda provider: "processor_exclude" in provider,
                PROVIDERS,
            ),
        ),
    ),
    [],
)

DATASOURCE_TYPE_PROVIDERS = sum(
    list(
        map(
            lambda entry: entry["datasource_packages"],
            filter(
                lambda provider: "datasource_packages" in provider,
                PROVIDERS,
            ),
        ),
    ),
    [],
)

DATASOURCE_PROCESSOR_EXCLUDE_LIST = sum(
    list(
        map(
            lambda entry: entry["datasource_processors_exclude"],
            filter(
                lambda provider: "datasource_processors_exclude" in provider,
                PROVIDERS,
            ),
        ),
    ),
    [],
)

APP_TEMPLATES_DIR = (
    os.getenv("APP_TEMPATES_DIR").split(",")
    if os.getenv(
        "APP_TEMPATES_DIR",
    )
    else [os.path.join(BASE_DIR, "contrib", "apps", "templates")]
)

SHEET_TEMPLATES_DIR = (
    os.getenv("SHEET_TEMPLATES_DIR").split(",")
    if os.getenv("SHEET_TEMPLATES_DIR")
    else [os.path.join(BASE_DIR, "contrib", "sheets")]
)

DATA_PIPELINES_DIR = (
    os.getenv("DATA_PIPELINES_DIR").split(",")
    if os.getenv("DATA_PIPELINES_DIR")
    else [
        os.path.join(BASE_DIR, "contrib", "data", "pipelines"),
    ]
)

STORE_APPS_DIR = (
    os.getenv("STORE_APPS_DIR").split(",")
    if os.getenv("STORE_APPS_DIR")
    else [
        os.path.join(BASE_DIR, "contrib", "apps"),
    ]
)

SOCIALACCOUNT_PROVIDERS = {
    "connection_google": {
        # For each OAuth based provider, either add a ``SocialApp``
        # (``socialaccount`` app) containing the required client
        # credentials, or list them here:
        "SCOPE": [
            "profile",
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/drive.readonly.metadata",
        ],
        "AUTH_PARAMS": {
            "access_type": "offline",
        },
        "APP": {
            "client_id": os.getenv("CONNECTION_GOOGLE_CLIENT_ID", ""),
            "secret": os.getenv("CONNECTION_GOOGLE_CLIENT_SECRET", ""),
            "key": os.getenv("CONNECTION_GOOGLE_CLIENT_KEY", ""),
        },
    },
}

EVENT_TOPIC_MAPPING = {
    "app.run.finished": [
        {
            "event_processor": "llmstack.events.consumers.app_run_finished.persist_app_run_history",
            "event_data_cls": "llmstack.events.consumers.app_run_finished.AppRunFinishedEventData",
        }
    ],
}

ANONYMOUS_USER_RATELIMIT = os.getenv("ANONYMOUS_USER_RATELIMIT", None)

LIMITER_MODULE = "llmstack.server.limiter"

ENABLE_JOBS = os.getenv("ENABLE_JOBS", "True") == "True"

CONNECTION_TYPE_INTERFACE_EXCLUDED_PACKAGES = os.getenv("CONNECTION_TYPE_INTERFACE_EXCLUDED_PACKAGES", "").split(",")

DEFAULT_DATA_DESTINATION_CONFIG = {"provider_slug": "weaviate", "processor_slug": "vector-store"}

DEFAULT_EMBEDDINGS_GENERATOR_CONFIG = {"provider_slug": "openai", "embedding_model_slug": "text-embedding-ada-002"}
