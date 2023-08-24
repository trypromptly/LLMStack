import os
from pathlib import Path

from django.utils.log import DEFAULT_LOGGING

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    'SECRET_KEY', 'django-insecure-o25+*nb2h8_f6t7_^r7r1e#_p@0b)0(i@-wr(h1@!enw^co2&m',
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv(
    'ALLOWED_HOSTS',
    '127.0.0.1,localhost',
).split(',')

LLMSTACK_PORT = os.getenv('LLMSTACK_PORT', 3000)

CSRF_TRUSTED_ORIGINS = os.getenv(
    'CSRF_TRUSTED_ORIGINS',
    f'http://127.0.0.1:{LLMSTACK_PORT},http://localhost:{LLMSTACK_PORT}',
).split(',')

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

CIPHER_KEY_SALT = os.getenv('CIPHER_KEY_SALT', None)

ADMIN_ENABLED = os.getenv('ADMIN_ENABLED', True)

DATA_UPLOAD_MAX_MEMORY_SIZE = os.getenv(
    'DATA_UPLOAD_MAX_MEMORY_SIZE', 26214400,
)  # 25MB default

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sites',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'processors.apps.ProcessorsConfig',
    'datasources.apps.DatasourcesConfig',
    'apps.apps.AppsConfig',
    'base.apps.BaseConfig',
    'organizations.apps.OrganizationsConfig',
    'flags',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'django_rq',
    'django_jsonform',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.authorization_middleware.AuthorizationMiddleware',
]

ROOT_URLCONF = 'llmstack.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'llmstack.wsgi.application'
ASGI_APPLICATION = 'llmstack.asgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.{}'.format(
            os.getenv('DATABASE_ENGINE', 'postgresql'),
        ),
        'NAME': os.getenv(
            'DATABASE_NAME', 'llmstack',
        ),
        'USER': os.getenv('DATABASE_USERNAME', 'llmstack'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'llmstack'),
        'HOST': os.getenv('DATABASE_HOST', 'postgres'),
        'PORT': os.getenv('DATABASE_PORT', 5432),
    },
}


AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

REACT_APP_DIR = os.path.join(BASE_DIR, 'client')
STATIC_URL = os.getenv('STATIC_URL', 'static/')
STATICFILES_DIRS = [
    os.path.join(REACT_APP_DIR, 'build', 'static'),
]
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
DEFAULT_FILE_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', os.getenv('LOG_LEVEL', 'ERROR')),
        },
        'rq.worker': {
            'handlers': ['console'],
            'level': os.getenv('RQ_LOG_LEVEL', os.getenv('LOG_LEVEL', 'ERROR')),
        },
    },
    'root': {
        'handlers': ['console'],
        'level': os.getenv('LOG_LEVEL', 'ERROR'),
    },
}

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'base.renderers.renderers.ORJSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f"redis://{os.getenv('REDIS_HOST', 'redis')}:{os.getenv('REDIS_PORT', 6379)}/1",
        'TIMEOUT': 3600,
    },
    'app_session': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://{os.getenv('REDIS_HOST', 'redis')}:{os.getenv('REDIS_PORT', 6379)}/2",
        'TIMEOUT': 3600,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
    },
    'app_session_data': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://{os.getenv('REDIS_HOST', 'redis')}:{os.getenv('REDIS_PORT', 6379)}/3",
        'TIMEOUT': 3600,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
    },
}

APP_SESSION_TIMEOUT = int(os.getenv('APP_SESSION_TIMEOUT', 3600))

ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
SITE_ID = 1
LOGIN_REDIRECT_URL = '/'
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_PROVIDERS = {}
ACCOUNT_ADAPTER = 'llmstack.adapters.CustomAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'llmstack.adapters.CustomSocialAccountAdapter'

DEFAULT_AWS_SECRET_ACCESS_KEY = os.getenv('DEFAULT_AWS_SECRET_ACCESS_KEY', '')
DEFAULT_AWS_DEFAULT_REGION = os.getenv('DEFAULT_AWS_DEFAULT_REGION', '')
DEFAULT_AWS_ACCESS_KEY_ID = os.getenv('DEFAULT_AWS_ACCESS_KEY_ID', '')
DEFAULT_AZURE_OPENAI_API_KEY = os.getenv('DEFAULT_AZURE_OPENAI_API_KEY', '')
DEFAULT_AZURE_OPENAI_ENDPOINT = os.getenv('DEFAULT_AZURE_OPENAI_ENDPOINT', '')
DEFAULT_OPENAI_API_KEY = os.getenv('DEFAULT_OPENAI_API_KEY', '')
DEFAULT_DREAMSTUDIO_API_KEY = os.getenv('DEFAULT_DREAMSTUDIO_API_KEY', '')
DEFAULT_COHERE_API_KEY = os.getenv('DEFAULT_COHERE_API_KEY', '')
DEFAULT_FOREFRONTAI_API_KEY = os.getenv('DEFAULT_FOREFRONTAI_API_KEY', '')
DEFAULT_ELEVENLABS_API_KEY = os.getenv('DEFAULT_ELEVENLABS_API_KEY', '')
DEFAULT_GOOGLE_SERVICE_ACCOUNT_JSON_KEY = os.getenv(
    'DEFAULT_GOOGLE_SERVICE_ACCOUNT_JSON_KEY', '{}',
)
DEFAULT_LOCALAI_API_KEY = os.getenv('DEFAULT_LOCALAI_API_KEY', '')
DEFAULT_LOCALAI_BASE_URL = os.getenv('DEFAULT_LOCALAI_BASE_URL', '')

WEAVIATE_URL = os.getenv('WEAVIATE_URL', 'http://weaviate:8080')
WEAVIATE_TEXT2VEC_MODULE_CONFIG = {
    'model': 'ada',
    'type': 'text',
}
WEAVIATE_EMBEDDINGS_API_RATE_LIMIT = 1000
WEAVIATE_EMBEDDINGS_BATCH_SIZE = 50
USE_CUSTOM_EMBEDDING = os.getenv('USE_CUSTOM_EMBEDDING', 'False') == 'True'

PLAYWRIGHT_URL = os.getenv('PLAYWRIGHT_URL', 'ws://playwright:30000/ws')

RQ_QUEUES = {
    'default': {
        'HOST': os.getenv('REDIS_HOST', 'redis'),
        'PORT': os.getenv('REDIS_PORT', 6379),
        'DB': os.getenv('REDIS_DB', 0),
        'DEFAULT_TIMEOUT': 1500,
    },
}

X_FRAME_OPTIONS = 'SAMEORIGIN'

SITENAME = os.getenv('SITENAME', 'Promptly')
SITE_URL = os.getenv('SITE_URL', 'https://trypromptly.com')

INDEX_VIEW_MODULE = 'base.views'
EMAIL_SENDER_CLASS = 'emails.sender.DefaultEmailSender'
HISTORY_STORE_CLASS = 'processors.history.DefaultHistoryStore'
EMAIL_TEMPLATE_FACTORY_CLASS = 'emails.templates.factory.DefaultEmailTemplateFactory'
FLAG_SOURCES = ['base.flags.FlagSource']

PROCESSOR_PROVIDERS = [
    'processors.providers.azure',
    'processors.providers.cohere',
    'processors.providers.elevenlabs',
    'processors.providers.google',
    'processors.providers.localai',
    'processors.providers.openai',
    'processors.providers.promptly',
    'processors.providers.stabilityai',
]

DATASOURCE_TYPE_PROVIDERS = [
    'datasources.handlers.amazon',
    'datasources.handlers.files',
    'datasources.handlers.google',
    'datasources.handlers.text',
    'datasources.handlers.website',
]
