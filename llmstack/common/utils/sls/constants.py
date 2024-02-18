import httpx

RAW_RESPONSE_HEADER = "X-Stainless-Raw-Response"
# default timeout is 10 minutes
DEFAULT_TIMEOUT = httpx.Timeout(timeout=600.0, connect=5.0)
DEFAULT_MAX_RETRIES = 2
DEFAULT_LIMITS = httpx.Limits(max_connections=100, max_keepalive_connections=20)

INITIAL_RETRY_DELAY = 0.5
MAX_RETRY_DELAY = 8.0

PROVIDER_OPENAI = "openai"
PROVIDER_GOOGLE = "google"
PROVIDER_AZURE_OPENAI = "azure-openai"
PROVIDER_STABILITYAI = "stabilityai"
PROVIDER_LOCALAI = "localai"
