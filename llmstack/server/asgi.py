import os
import sys
from os.path import abspath, dirname, join

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path

from llmstack.server.consumers import (
    AppConsumer,
    AssetStreamConsumer,
    ConnectionConsumer,
    PlaygroundConsumer,
    StoreAppConsumer,
)
from llmstack.sheets.consumers import SheetAppConsumer, SheetBuilderConsumer

BASE_DIR = dirname(dirname(abspath(__file__)))
sys.path.append(join(BASE_DIR, "llmstack"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "llmstack.server.settings")

django_asgi_app = get_asgi_application()


application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(
                [
                    path("ws/apps/<str:app_uuid>", AppConsumer.as_asgi()),
                    path("ws/apps/<str:app_uuid>/<str:preview>", AppConsumer.as_asgi()),
                    path("ws/assets/<str:category>/<str:uuid>", AssetStreamConsumer.as_asgi()),
                    path(
                        "ws/connections/<str:conn_id>/activate",
                        ConnectionConsumer.as_asgi(),
                    ),
                    path("ws/playground", PlaygroundConsumer.as_asgi()),
                    path("ws/store/apps/<str:app_id>", StoreAppConsumer.as_asgi()),
                    path("ws/sheets/<str:sheet_id>/run/<str:run_id>", SheetAppConsumer.as_asgi()),
                    path("ws/sheets/<str:sheet_id>/builder", SheetBuilderConsumer.as_asgi()),
                ],
            ),
        ),
    },
)
