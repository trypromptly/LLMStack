from collections import namedtuple

from llmstack.apps.handlers.app_runnner import AppRunner

PlatformApp = namedtuple(
    "PlatformApp",
    ["id", "uuid", "type", "web_integration_config", "is_published"],
)

PlatformAppType = namedtuple("PlatformAppType", ["slug"])


class PlatformAppRunner(AppRunner):
    def _is_app_accessible(self):
        return True
