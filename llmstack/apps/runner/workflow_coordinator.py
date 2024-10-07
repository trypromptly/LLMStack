import logging
from typing import Dict, List

from llmstack.apps.runner.app_coordinator import AppCoordinator
from llmstack.play.actor import ActorConfig
from llmstack.play.output_stream import Message, MessageType

logger = logging.getLogger(__name__)


class WorkflowCoordinator(AppCoordinator):
    def __init__(self, actor_configs: List[ActorConfig], output_template: str = ""):
        super().__init__(actor_configs, output_template)

        # Build dependency graph
        for ac in actor_configs:
            for dep in ac.dependencies:
                self._actor_dependents[dep].add(ac.name)

        # Start actors that have no dependencies and send a BEGIN message
        for actor_config in actor_configs:
            if not self._actor_dependencies[actor_config.name]:
                actor_id = actor_config.name
                self.actors[actor_id] = actor_config.actor.start(
                    id=actor_id,
                    coordinator_urn=self.actor_urn,
                    dependencies=actor_config.dependencies,
                    **actor_config.kwargs,
                )
                self.tell_actor(actor_id, Message(type=MessageType.BEGIN))

    def relay(self, message: Message):
        if message.message_type == MessageType.BOOKKEEPING:
            self.bookkeeping_data_map[message.message_from] = message.message

            # If we have received all the bookkeeping data, then stop the coordinator
            if len(self.bookkeeping_data_map) == len(self.actors):
                # TODO: persist the bookkeeping data
                self.stop_actors()
            return

        logger.info(f"Relaying message {message} to {self._actor_dependents.get(message.message_from)}")

        # Relay message to all dependents
        for dependent in self._actor_dependents.get(message.message_from, set()):
            self.tell_actor(dependent, message)

    def get_dependents_map(self) -> Dict[str, List[str]]:
        return self._actor_dependents

    def get_dependencies_map(self) -> Dict[str, List[str]]:
        return self._actor_dependencies
