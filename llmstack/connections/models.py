import datetime
import uuid
from enum import Enum
from typing import Optional

from pydantic import BaseModel

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
    status: ConnectionStatus = ConnectionStatus.CREATED
    configuration: dict = {}
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    last_checked_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True

    def __str__(self):
        return f"{self.name} ({self.id})"


class ConnectionActivationOutput(BaseModel):
    data: dict


class ConnectionActivationInput(BaseModel):
    data: Optional[str] = None
