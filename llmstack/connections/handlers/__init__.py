from typing import Optional

from llmstack.common.blocks.base.schema import BaseSchema


class Oauth2BaseConfiguration(BaseSchema):
    token: Optional[str] = None
    token_type: Optional[str] = None
    expires_in: Optional[int] = None
    expires_at: Optional[str] = None
    refresh_token: Optional[str] = None

    def set_expires_at(self):
        import datetime

        if not self.expires_in:
            return

        time_now = datetime.datetime.now(datetime.timezone.utc)
        expires_at = time_now + datetime.timedelta(seconds=self.expires_in)
        self.expires_at = expires_at.isoformat()

    @property
    def is_expired(self) -> bool:
        import datetime

        if self.expires_at is None:
            return False

        time_now = datetime.datetime.now(datetime.timezone.utc)
        expires_at = datetime.datetime.fromisoformat(self.expires_at)
        return time_now > expires_at
