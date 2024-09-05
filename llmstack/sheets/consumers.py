import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django_redis import get_redis_connection

logger = logging.getLogger(__name__)

sheet_run_data_store = get_redis_connection("sheet_run_data_store")


@database_sync_to_async
def _get_sheet(sheet_id, user):
    from llmstack.base.models import Profile
    from llmstack.sheets.models import PromptlySheet

    profile = Profile.objects.get(user=user)
    return PromptlySheet.objects.get(uuid=sheet_id, profile_uuid=profile.uuid)


class SheetAppConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.sheet_id = self.scope["url_route"]["kwargs"]["sheet_id"]
        self.run_id = self.scope["url_route"]["kwargs"]["run_id"]
        self._user = self.scope.get("user", None)

        sheet = await _get_sheet(self.sheet_id, self._user)

        if not sheet or sheet.extra_data.get("run_id") != self.run_id:
            logger.error(f"Sheet {self.sheet_id} not found or run id mismatch")
            await self.close()
            return

        # Add this channel to the group
        await self.channel_layer.group_add(self.run_id, self.channel_name)
        await self.accept()

        # Stream old events from redis
        events = sheet_run_data_store.lrange(self.run_id, 0, -1)
        for event in events:
            await self.send(text_data=event.decode("utf-8"))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.run_id, self.channel_name)

    async def close(self, code=None, reason=None):
        await self.disconnect(code)
        await super().close(code)

    async def cell_update(self, event):
        await self.send(text_data=json.dumps(event))
        await self._append_event_to_redis(event)

    async def cell_updating(self, event):
        await self.send(text_data=json.dumps(event))

    async def cell_error(self, event):
        await self.send(text_data=json.dumps(event))

    async def sheet_status(self, event):
        await self.send(text_data=json.dumps(event))

    async def sheet_update(self, event):
        await self.send(text_data=json.dumps(event))
        await self._append_event_to_redis(event)

    async def sheet_disconnect(self, event):
        await self.send(text_data=json.dumps(event))
        await self.channel_layer.group_discard(self.run_id, self.channel_name)

    async def sheet_error(self, event):
        await self.send(text_data=json.dumps(event))
        await self.channel_layer.group_discard(self.run_id, self.channel_name)

    async def _append_event_to_redis(self, event):
        try:
            sheet_run_data_store.rpush(self.run_id, json.dumps(event))
        except Exception as e:
            logger.error(f"Error appending event to Redis: {str(e)}")
