import uuid

from llmstack.apps.models import App, AppType

from .types.app_type_interface import AppTypeInterface

# Import all app types here
from .types.chat import ChatApp  # noqa: F401
from .types.discord import DiscordApp  # noqa: F401
from .types.slack import SlackApp  # noqa: F401
from .types.twilio_sms import TwilioSmsApp  # noqa: F401
from .types.web import WebApp  # noqa: F401


class AppTypeFactory:
    """
    Factory class for App types
    """

    @staticmethod
    def get_app_type_handler(
        app_type: AppType,
        platform: str = None,
    ) -> AppTypeInterface:
        subclasses = AppTypeInterface.__subclasses__()
        # Match with platform
        if platform:
            for subclass in subclasses:
                # Convert to lowercase to avoid case sensitivity
                if subclass.slug().lower() == platform.lower():
                    return subclass

        # Match with slug
        for subclass in subclasses:
            if subclass.slug() == app_type.slug.lower():
                return subclass

        return None

    @staticmethod
    def get_app_type_signature_verifier(app_id: str, platform: str = "web"):
        app = App.objects.get(uuid=uuid.UUID(app_id))
        app_type_handler = AppTypeFactory.get_app_type_handler(
            app.type,
            platform,
        )

        return app, app_type_handler.verify_request_signature
