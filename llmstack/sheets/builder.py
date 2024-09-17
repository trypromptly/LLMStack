import logging

logger = logging.getLogger(__name__)


class SheetBuilder:
    def __init__(self, sheet, model_provider_slug="openai", model_slug="gpt-4o-mini"):
        self.sheet = sheet
        self.model_provider_slug = model_provider_slug
        self.model_slug = model_slug

        if not self.sheet:
            raise ValueError("Invalid sheet")

    def process_event(self, event):
        event_type = event.get("type")
        if event_type == "connect":
            return event
        elif event_type == "message":
            return {"type": "message", "message": f"HELLO s{event.get('message')}"}

        return event

    def close(self):
        pass
