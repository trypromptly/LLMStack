import asyncio
import logging
from typing import Any, Dict, List, Set

from pykka import ThreadingActor

from llmstack.apps.runner.agent_actor import AgentActor
from llmstack.apps.runner.input_actor import InputActor
from llmstack.apps.runner.output_actor import OutputActor
from llmstack.play.actor import ActorConfig
from llmstack.play.messages import ContentData
from llmstack.play.output_stream import Message, MessageType

logger = logging.getLogger(__name__)


class AppCoordinator(ThreadingActor):
    def __init__(
        self,
        actor_configs: List[ActorConfig],
        output_template: str = "",
        is_agent: bool = False,
        is_voice_agent: bool = False,
        env: Dict[str, Any] = {},
        config: Dict[str, Any] = {},
        spread_output_for_keys: Set[str] = set(),
        bookkeeping_queue: asyncio.Queue = None,
        metadata: Dict[str, Any] = {},
    ):
        super().__init__()

        self._bookkeeping_queue = bookkeeping_queue

        # Make sure there are no duplicate names in actor_configs
        assert len(set([actor_config.name for actor_config in actor_configs])) == len(
            actor_configs,
        )

        # Make sure none of the actor_config names are in ["input", "output", "agent"]
        for actor_config in actor_configs:
            if actor_config.name in ["_inputs0", "input", "output", "agent", "coordinator"]:
                raise ValueError(f"Actor config name {actor_config.name} is reserved")

        self._actor_configs_map = {actor_config.name: actor_config for actor_config in actor_configs}

        self._is_agent = is_agent
        self._is_voice_agent = is_voice_agent

        # Map of actor id to actor
        self.actors = {
            "_inputs0": InputActor.start(
                coordinator_urn=self.actor_urn,
                bookkeeping_queue=self._bookkeeping_queue,
            )
        }

        # Add agent actor for output if it's an agent
        if self._is_agent or self._is_voice_agent:
            self.actors["output"] = AgentActor.start(
                coordinator_urn=self.actor_urn,
                dependencies=["_inputs0"] + list(self._actor_configs_map.keys()),
                templates={
                    **{ac.name: ac.kwargs.get("output_template", {}).get("markdown", "") for ac in actor_configs},
                },
                agent_config=config,
                is_voice_agent=self._is_voice_agent,
                metadata=metadata,
                provider_configs=env.get("provider_configs", {}),
                tools=list(map(lambda x: x.tool_schema, actor_configs)),
                bookkeeping_queue=self._bookkeeping_queue,
            )
        else:
            self.actors["output"] = OutputActor.start(
                coordinator_urn=self.actor_urn,
                dependencies=["_inputs0"] + list(self._actor_configs_map.keys()),
                templates={"output": output_template},
                spread_output_for_keys=spread_output_for_keys,
                bookkeeping_queue=self._bookkeeping_queue,
            )

        self._actor_dependencies = {ac.name: set(ac.dependencies) for ac in actor_configs}
        self._actor_dependencies["output"] = set(["_inputs0"] + list(self._actor_configs_map.keys()))
        self._actor_dependencies["_inputs0"] = set()

        self._actor_dependents = {ac.name: set() for ac in actor_configs}
        self._actor_dependents["_inputs0"] = set(["output"])
        self._actor_dependents["output"] = set()

        # Update dependents based on dependencies
        for actor, deps in self._actor_dependencies.items():
            for dep in deps:
                if dep in self._actor_dependents:
                    self._actor_dependents[dep].add(actor)

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
                bookkeeping_queue=self._bookkeeping_queue,
                **self._actor_configs_map[actor_id_prefix].kwargs,
            )

        if message.type == MessageType.BEGIN or message.type == MessageType.CONTENT:
            self._bookkeeping_queue.put_nowait((actor_id, None))

        self.actors[actor_id].tell(message)

    def relay(self, message: Message):
        actor_id = message.sender.split("/")[0]
        logger.debug(f"Relaying message {message} to {self._actor_dependents.get(actor_id)}")

        # Relay message to all dependents
        for dependent in self._actor_dependents.get(actor_id, set()):
            self.tell_actor(dependent, message)

        # Send to message.receiver if we have not already sent to it
        if message.receiver != "coordinator" and message.receiver not in self._actor_dependents.get(actor_id, set()):
            self.tell_actor(message.receiver, message)

    def input(self, request_id: str, data: Dict):
        message = Message(
            id=request_id,
            type=MessageType.CONTENT,
            sender="coordinator",
            receiver="_inputs0",
            data=ContentData(content=data),
        )

        # Reset actors before handling new input
        self.reset_actors()

        self.tell_actor("_inputs0", message)

        # Also start actors that have no dependencies and send a BEGIN message when not an agent
        if not self._is_agent and not self._is_voice_agent:
            for actor_config in self._actor_configs_map.values():
                if not self._actor_dependencies[actor_config.name]:
                    actor_id = actor_config.name
                    self.actors[actor_id] = actor_config.actor.start(
                        id=actor_id,
                        coordinator_urn=self.actor_urn,
                        dependencies=actor_config.dependencies,
                        bookkeeping_queue=self._bookkeeping_queue,
                        **actor_config.kwargs,
                    )
                    self.tell_actor(
                        actor_id,
                        Message(id=request_id, type=MessageType.BEGIN, sender="coordinator", receiver=actor_id),
                    )

    async def output(self):
        return await self.actors["output"].proxy().get_output()

    def bookkeeping_data(self):
        return self.actors["output"].proxy().get_bookkeeping_data().get()

    def on_stop(self):
        logger.info("Coordinator is stopping")
        self.stop_actors()
        super().on_stop()

    def stop_actors(self):
        logger.info("Stopping actors")
        for actor in self.actors.values():
            actor.stop()

    def reset_actors(self):
        for actor in self.actors.values():
            actor.proxy().reset().get()
