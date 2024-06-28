import orjson as json
from pydantic import BaseModel


class Config(BaseModel):
    """
    Base class for config type models stored in the database. Supports optional encryption.
    """

    config_type: str
    is_encrypted: bool = False
    data: str = ""

    def to_dict(self, encrypt_fn):
        return {
            "config_type": self.config_type,
            "is_encrypted": self.is_encrypted,
            "data": self.get_data(encrypt_fn),
        }

    def from_dict(self, dict_data, decrypt_fn):
        self.config_type = dict_data.get("config_type")
        self.is_encrypted = dict_data.get("is_encrypted")
        self.set_data(dict_data.get("data"), decrypt_fn)

        # Use the data from the dict to populate the fields
        self.__dict__.update(json.loads(self.data))

        return self.model_dump(exclude={"is_encrypted", "config_type", "data"})

    def get_data(self, encrypt_fn):
        data = self.json(exclude={"is_encrypted", "config_type", "data"})
        return encrypt_fn(data).decode("utf-8") if self.is_encrypted else data

    def set_data(self, data, decrypt_fn):
        self.data = data
        if self.is_encrypted:
            self.data = decrypt_fn(data)
