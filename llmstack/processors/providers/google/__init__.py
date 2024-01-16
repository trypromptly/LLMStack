import json
from google.oauth2 import service_account
from google.auth.transport.requests import Request

JWT_TOKEN = 'jwt_token'
API_KEY = 'api_key'


def get_google_credential_from_env(env: str) -> dict:
    data = env['google_service_account_json_key']
    try:
        google_service_account_json_key = json.loads(data)
        credentials = service_account.Credentials.from_service_account_info(
            google_service_account_json_key
        )
        credentials = credentials.with_scopes(
            ['https://www.googleapis.com/auth/cloud-platform'])
        credentials.refresh(Request())
        token = credentials.token, JWT_TOKEN
        return token, JWT_TOKEN
    except json.JSONDecodeError:
        return data, API_KEY


def get_project_id_from_env(env: str) -> str:
    data = env['google_service_account_json_key']
    try:
        google_service_account_json_key = json.loads(data)
        return google_service_account_json_key['project_id']
    except json.JSONDecodeError:
        return None
