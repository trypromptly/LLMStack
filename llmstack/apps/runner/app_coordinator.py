import logging
import uuid
from typing import Dict, List

from pykka import ThreadingActor

from llmstack.play.actor import ActorConfig
from llmstack.play.actors.input import InputActor
from llmstack.play.actors.output import OutputActor
from llmstack.play.output_stream import Message, MessageType

logger = logging.getLogger(__name__)


class AppCoordinator(ThreadingActor):
    def __init__(self, actor_configs: List[ActorConfig], output_template: str = ""):
        super().__init__()

        # Make sure there are no duplicate names in actor_configs
        assert len(set([actor_config.name for actor_config in actor_configs])) == len(
            actor_configs,
        )

        # Make sure none of the actor_config names are in ["input", "output", "agent"]
        for actor_config in actor_configs:
            if actor_config.name in ["input", "output", "agent", "coordinator"]:
                raise ValueError(f"Actor config name {actor_config.name} is reserved")

        self._actor_configs_map = {actor_config.name: actor_config for actor_config in actor_configs}

        # Map of actor id to actor
        self.actors = {
            "input": InputActor.start(
                coordinator_urn=self.actor_urn,
            ),
            "output": OutputActor.start(
                coordinator_urn=self.actor_urn,
                dependencies=["input"] + list(self._actor_configs_map.keys()),
                template=output_template,
            ),
        }

        self._actor_dependencies = {ac.name: set(ac.dependencies) for ac in actor_configs}
        self._actor_dependencies["output"] = set(["input"] + list(self._actor_configs_map.keys()))
        self._actor_dependencies["input"] = set()

        self._actor_dependents = {ac.name: set() for ac in actor_configs}
        self._actor_dependents["input"] = set(list(self._actor_configs_map.keys()) + ["output"])
        self._actor_dependents["output"] = set()

        # Update dependents based on dependencies
        for actor, deps in self._actor_dependencies.items():
            for dep in deps:
                if dep in self._actor_dependents:
                    self._actor_dependents[dep].add(actor)

        # Bookkeeping
        self.bookkeeping_data_map = {}

    def tell_actor(self, actor_id: str, message: Message):
        if actor_id not in self.actors:
            if "/" in actor_id:
                actor_id_prefix = actor_id.split("/")[0]
            else:
                actor_id_prefix = actor_id

            logger.info(f"Starting actor {actor_id}")
            self.actors[actor_id] = self._actor_configs_map[actor_id_prefix].actor.start(
                id=actor_id,
                coordinator_urn=self.actor_urn,
                dependencies=self._actor_configs_map[actor_id_prefix].dependencies,
                **self._actor_configs_map[actor_id_prefix].kwargs,
            )

        self.actors[actor_id].tell(message)

    def input(self, data: Dict, message_id: str = None):
        message = Message(
            message_id=message_id or str(uuid.uuid4()),
            message_type=MessageType.STREAM_CLOSED,
            message=data,
            message_from="coordinator",
            message_to="input",
        )

        # Reset output actor before sending input
        self.actors["output"].proxy().reset().get()

        self.tell_actor("input", message)

    def output(self):
        return self.actors["output"].proxy().get_output().get()

    def output_stream(self):
        return self.actors["output"].proxy().get_output_stream().get()

    def on_stop(self):
        logger.info("Coordinator is stopping")
        self.stop_actors()
        super().on_stop()

    def stop_actors(self):
        logger.info("Stopping actors")
        for actor in self.actors.values():
            actor.stop()
