import json

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from pydantic import Field

from llmstack.processors.providers.config import ProviderConfig

JWT_TOKEN = "jwt_token"
API_KEY = "api_key"


def get_google_credentials_from_json_key(json_key: str) -> dict:
    try:
        google_service_account_json_key = json.loads(json_key)
        credentials = service_account.Credentials.from_service_account_info(
            google_service_account_json_key,
        )
        credentials = credentials.with_scopes(
            ["https://www.googleapis.com/auth/cloud-platform"],
        )
        credentials.refresh(Request())
        token = credentials.token, JWT_TOKEN
        return token, JWT_TOKEN
    except json.JSONDecodeError:
        return json_key, API_KEY
    except Exception:
        return None, None


def get_google_credential_from_env(env: str) -> dict:
    data = env["google_service_account_json_key"]
    return get_google_credentials_from_json_key(data)


def get_project_id_from_json_key(json_key: str) -> dict:
    try:
        google_service_account_json_key = json.loads(json_key)
        return google_service_account_json_key["project_id"]
    except json.JSONDecodeError:
        return None


def get_project_id_from_env(env: str) -> str:
    data = env["google_service_account_json_key"]
    return get_project_id_from_json_key(data)


class GoogleProviderConfig(ProviderConfig):
    provider_slug: str = "google"
    api_key: str = Field(
        title="API Key",
        description="Google Gemini API Key",
        default="",
        json_schema_extra={"widget": "password", "advanced_parameter": False},
    )
    service_account_json_key: str = Field(
        title="Service Account JSON",
        description="Google Service Account JSON",
        default="",
        json_schema_extra={"widget": "textarea", "advanced_parameter": True},
    )
