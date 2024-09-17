import datetime
import logging
from typing import List, Literal, Optional, Union

import requests
from pydantic import BaseModel, Field

from llmstack.common.blocks.base.schema import BaseSchema
from llmstack.connections.models import ConnectionType
from llmstack.connections.types import ConnectionTypeInterface

logger = logging.getLogger(__name__)


class HeaderKeyValueType(BaseModel):
    key: str
    value: str


class RefreshToken(BaseModel):
    grant_type: Literal["refresh_token"] = Field(default="refresh_token", json_schema_extra={"widget": "hidden"})
    refresh_token: str = Field(json_schema_extra={"widget": "textarea"}, description="Refresh Token", default="")
    headers: Optional[List[HeaderKeyValueType]] = Field(
        default=[HeaderKeyValueType(key="Content-Type", value="application/x-www-form-urlencoded")],
        description="Provide additional headers to be sent with the refresh token request",
    )

    @property
    def is_expired(self):
        return datetime.datetime.now(datetime.timezone.utc).timestamp() > self.expires_at

    @property
    def headers_dict(self):
        return {header.key: header.value for header in self.headers}


class AuthorizationCode(BaseModel):
    grant_type: Literal["authorization_code"] = Field(
        default="authorization_code", json_schema_extra={"widget": "hidden"}
    )
    code: str = Field(json_schema_extra={"widget": "textarea"}, description="Authorization Code")
    redirect_uri: str = Field(json_schema_extra={"widget": "textarea"}, description="Redirect URI")


class ClientCredentials(BaseModel):
    grant_type: Literal["client_credentials"] = Field(
        default="client_credentials", json_schema_extra={"widget": "hidden"}
    )


class OAuth2AuthenticationConfiguration(BaseSchema):
    token_url: str
    grant_type: Union[RefreshToken, AuthorizationCode, ClientCredentials] = Field(
        default=RefreshToken(), description="Grant Type"
    )
    client_id: Optional[str] = Field(default=None, description="Client ID")
    client_secret: Optional[str] = Field(default=None, description="Client Secret")

    expires_at: Optional[float] = Field(
        default=None, description="Token Expiry Time", json_schema_extra={"widget": "hidden"}
    )
    token: Optional[str] = Field(default=None, json_schema_extra={"widget": "hidden"})
    token_prefix: str = "Bearer"


class OAuth2AuthenticationBasedAPILogin(ConnectionTypeInterface[OAuth2AuthenticationConfiguration]):
    @staticmethod
    def name() -> str:
        return "OAuth2 Token Authentication"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    @staticmethod
    def slug() -> str:
        return "oauth2_authentication"

    @staticmethod
    def description() -> str:
        return "OAuth2 Refresh Token based API authentication"

    @staticmethod
    def type() -> ConnectionType:
        return ConnectionType.CREDENTIALS

    @classmethod
    def parse_config(cls, config: dict) -> OAuth2AuthenticationConfiguration:
        if config.get("grant_type", {}).get("grant_type") == "refresh_token":
            expires_at = config.get("expires_at", None)
            if expires_at is None or datetime.datetime.now(datetime.timezone.utc).timestamp() > expires_at:
                refresh_token = config.get("grant_type", {}).get("refresh_token")
                headers_list = config.get("grant_type", {}).get("headers")
                headers = {header["key"]: header["value"] for header in headers_list}
                config = cls.refresh_token(refresh_token, headers, config)
        elif config.get("grant_type", {}).get("grant_type") == "authorization_code":
            code = config.get("grant_type", {}).get("code")
            redirect_uri = config.get("grant_type", {}).get("redirect_uri")
            config = cls.authorization_code(code, redirect_uri, config)
        elif config.get("grant_type", {}).get("grant_type") == "client_credentials":
            config = cls.client_credentials(config)
        return OAuth2AuthenticationConfiguration.model_validate(config)

    @classmethod
    def refresh_token(cls, refresh_token, headers, configuration):
        payload = {
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        if configuration.get("client_id"):
            payload["client_id"] = configuration["client_id"]
        if configuration.get("client_secret"):
            payload["client_secret"] = configuration["client_secret"]

        token_url = configuration["token_url"]
        response = requests.post(token_url, data=payload, headers=headers)
        if response.status_code == 200:
            access_token = response.json().get("access_token")
            expires_in = int(response.json().get("expires_in"))
            refresh_token = response.json().get("refresh_token")
            expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=expires_in)
            configuration["token"] = access_token
            configuration["expires_at"] = expires_at.timestamp()
            if refresh_token:
                configuration["grant_type"] = {
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                }
            return configuration
        else:
            return None

    @classmethod
    def authorization_code(cls, code, redirect_uri, configuration):
        payload = {
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
        if configuration.get("client_id"):
            payload["client_id"] = configuration["client_id"]
        if configuration.get("client_secret"):
            payload["client_secret"] = configuration["client_secret"]

        token_url = configuration["token_url"]
        response = requests.post(token_url, data=payload)
        if response.status_code == 200:
            access_token = response.json().get("access_token")
            expires_in = int(response.json().get("expires_in"))
            refresh_token = response.json().get("refresh_token")
            expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=expires_in)
            configuration["token"] = access_token
            configuration["expires_at"] = expires_at.timestamp()
            if refresh_token:
                configuration["grant_type"] = {
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                }
            return configuration
        else:
            return None

    @classmethod
    def client_credentials(cls, configuration):
        payload = {
            "grant_type": "client_credentials",
        }
        if configuration.get("client_id"):
            payload["client_id"] = configuration["client_id"]
        if configuration.get("client_secret"):
            payload["client_secret"] = configuration["client_secret"]

        token_url = configuration["token_url"]
        response = requests.post(token_url, data=payload)
        if response.status_code == 200:
            access_token = response.json().get("access_token")
            expires_in = int(response.json().get("expires_in"))
            expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=expires_in)
            configuration["token"] = access_token
            configuration["expires_at"] = expires_at.timestamp()
            return configuration
        else:
            return None
