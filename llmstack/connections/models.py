import datetime
import uuid
from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator

"""
We use pydantic models to represent the connection information and save it in the database as encrypted json.
"""


class ConnectionStatus(str, Enum):
    CREATED = "Created"
    CONNECTING = "Connecting"
    ACTIVE = "Active"
    FAILED = "Failed"

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value


class ConnectionType(str, Enum):
    BROWSER_LOGIN = "browser_login"
    OAUTH2 = "oauth2"
    CREDENTIALS = "credentials"


class Connection(BaseModel):
    """
    Connection model
    """

    name: str
    id: str = str(uuid.uuid4())
    description: str = ""
    base_connection_type: ConnectionType = ConnectionType.BROWSER_LOGIN
    connection_type_slug: str
    provider_slug: str
    status: ConnectionStatus = "Created"
    configuration: dict = {}
    created_at: datetime.datetime = None
    updated_at: datetime.datetime = None
    last_checked_at: datetime.datetime = None

    @field_validator("created_at", "updated_at", "last_checked_at")
    def datetime_to_string(cls, value):
        return value.isoformat() if value else None

    class Config:
        from_attributes = True

    def __str__(self):
        return f"{self.name} ({self.id})"


class ConnectionActivationOutput(BaseModel):
    data: dict


class ConnectionActivationInput(BaseModel):
    data: Optional[str] = None
