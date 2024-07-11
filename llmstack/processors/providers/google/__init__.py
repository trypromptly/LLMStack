import json

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from pydantic import Field

from llmstack.processors.providers.config import ProviderConfig

JWT_TOKEN = "jwt_token"
API_KEY = "api_key"


def get_google_credential_from_env(env: str) -> dict:
    data = env["google_service_account_json_key"]
    try:
        google_service_account_json_key = json.loads(data)
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
        return data, API_KEY
    except Exception:
        return None, None


def get_project_id_from_env(env: str) -> str:
    data = env["google_service_account_json_key"]
    try:
        google_service_account_json_key = json.loads(data)
        return google_service_account_json_key["project_id"]
    except json.JSONDecodeError:
        return None


class GoogleProviderConfig(ProviderConfig):
    provider_slug: str = "google"
    service_account_json_key: str = Field(
        title="Service Account JSON Key",
        description="Google Service Account JSON Key",
        default="",
        json_schema_extra={"widget": "password", "advanced_parameter": False},
    )
