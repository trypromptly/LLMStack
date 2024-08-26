import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


@database_sync_to_async
def update_sheet_channel_name(sheet_id, channel_name):
    from llmstack.sheets.models import PromptlySheet

    # Update the channel name for the sheet
    sheet = PromptlySheet.objects.get(uuid=sheet_id)
    sheet_extra_data = sheet.extra_data or {}
    sheet_extra_data["channel_name"] = channel_name
    sheet.extra_data = sheet_extra_data
    sheet.save(update_fields=["extra_data"])


class SheetAppConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.sheet_id = self.scope["url_route"]["kwargs"]["sheet_id"]
        self.run_id = self.scope["url_route"]["kwargs"]["run_id"]
        self._user = self.scope.get("user", None)
        # Update the channel name for the sheet
        await self.channel_layer.group_add(self.run_id, self.channel_name)
        await super().connect()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.run_id, self.channel_name)

    async def close(self, code=None, reason=None):
        await update_sheet_channel_name(self.sheet_id, None)
        await super().close(code, reason)

    async def cell_update(self, event):
        await self.send(text_data=json.dumps(event))

    async def cell_updating(self, event):
        await self.send(text_data=json.dumps(event))

    async def cell_error(self, event):
        await self.send(text_data=json.dumps(event))

    async def sheet_status(self, event):
        await self.send(text_data=json.dumps(event))

    async def sheet_update(self, event):
        await self.send(text_data=json.dumps(event))
