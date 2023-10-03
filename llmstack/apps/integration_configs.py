from typing import Optional

import orjson as json
from pydantic import BaseModel


class AppIntegrationConfig(BaseModel):
    """
    Base class for app integration config stored in the database. Optionally encrypted.
    """
    config_type: str
    is_encrypted: bool = False
    data: str = ''

    def to_dict(self, encrypt_fn):
        return {
            'config_type': self.config_type,
            'is_encrypted': self.is_encrypted,
            'data': self.get_data(encrypt_fn),
        }

    def from_dict(self, dict_data, decrypt_fn):
        self.config_type = dict_data.get('config_type')
        self.is_encrypted = dict_data.get('is_encrypted')
        self.set_data(dict_data.get('data'), decrypt_fn)

        # Use the data from the dict to populate the fields
        self.__dict__.update(json.loads(self.data))

        return self.dict(exclude={'is_encrypted', 'config_type', 'data'})

    def get_data(self, encrypt_fn):
        data = self.json(exclude={'is_encrypted', 'config_type', 'data'})
        return encrypt_fn(data).decode('utf-8') if self.is_encrypted else data

    def set_data(self, data, decrypt_fn):
        self.data = data
        if self.is_encrypted:
            self.data = decrypt_fn(data)


class WebIntegrationConfig(AppIntegrationConfig):
    config_type = 'web'
    is_encrypted = False
    allowed_sites: list = []
    domain: Optional[str] = None


class SlackIntegrationConfig(AppIntegrationConfig):
    config_type = 'slack'
    is_encrypted = True
    app_id: str = ''
    bot_token: str = ''
    verification_token: str = ''
    signing_secret: str = ''


class DiscordIntegrationConfig(AppIntegrationConfig):
    config_type = 'discord'
    is_encrypted = True
    app_id: str = ''
    slash_command_name: str = ''
    slash_command_description: str = ''
    bot_token: str = ''
    public_key: str = ''
    slash_command_id: Optional[str] = None
    
class TwilioIntegrationConfig(AppIntegrationConfig):
    config_type = 'twilio'
    is_encrypted = True
    account_sid: str = ''
    auth_token: str = ''
    phone_numbers: list = []
    
