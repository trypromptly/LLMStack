import datetime
import uuid
from enum import Enum
from pydantic import BaseModel, validator

"""
We use pydantic models to represent the connection information and save it in the database as encrypted json.
"""


class ConnectionStatus(str, Enum):
    CREATED = 'Created'
    CONNECTING = 'Connecting'
    ACTIVE = 'Active'
    FAILED = 'Failed'

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value


class Connection(BaseModel):
    """
    Connection model
    """
    name: str
    id: str = str(uuid.uuid4())
    description: str = ''
    connection_type_slug: str
    provider_slug: str
    status: ConnectionStatus = 'Created'
    configuration: dict = {}
    created_at: datetime.datetime = None
    updated_at: datetime.datetime = None
    last_checked_at: datetime.datetime = None

    @validator('created_at', 'updated_at', 'last_checked_at')
    def datetime_to_string(cls, value):
        return value.isoformat() if value else None

    class Config:
        orm_mode = True

    def __str__(self):
        return f'{self.name} ({self.id})'
