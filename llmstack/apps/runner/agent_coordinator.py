from typing import List

from llmstack.apps.runner.app_coordinator import AppCoordinator
from llmstack.play.actor import ActorConfig


class AgentCoordinator(AppCoordinator):
    def __init__(self, actor_configs: List[ActorConfig], output_template: str = ""):
        super().__init__(actor_configs, output_template)
