import logging
from typing import List

from pykka import ActorDeadError, ThreadingActor

from llmstack.play.actor import ActorConfig
from llmstack.play.output_stream import Message, MessageType, OutputStream
from llmstack.play.utils import ResettableTimer

logger = logging.getLogger(__name__)

TIMEOUT = 120


class Coordinator(ThreadingActor):
    def __init__(self, session_id, actor_configs: List[ActorConfig]):
        super().__init__()
        self._session_id = session_id
        self._stream_errors = {}

        # Make sure there are not duplicate names or template_keys in
        # actor_configs
        assert len(set([actor_config.name for actor_config in actor_configs])) == len(
            actor_configs,
        )

        assert len(set([actor_config.template_key for actor_config in actor_configs])) == len(
            actor_configs,
        )

        self._actor_configs = {actor_config.name: actor_config for actor_config in actor_configs}

        # Create output_streams
        self._output_streams = []

        all_dependencies = [actor_config.template_key for actor_config in actor_configs]
        # Spawn actors
        self.actors = {}
        for actor_config in actor_configs:
            self._output_streams.append(
                OutputStream(
                    stream_id=actor_config.name,
                    coordinator_urn=self.actor_urn,
                    output_cls=actor_config.output_cls,
                ),
            )
            actor = actor_config.actor.start(
                output_stream=self._output_streams[-1],
                dependencies=actor_config.dependencies,
                all_dependencies=all_dependencies,
                **actor_config.kwargs,
            )
            self.actors[actor_config.name] = actor
            logger.info(
                f"Spawned actor {actor} for coordinator {self.actor_urn}",
            )

        # Get dependencies for each actor and build a map of actor_urn ->
        # [actor_urn]
        self._actor_dependencies = {
            actor_config.name: set() for actor_config in actor_configs
        }  # Actors that this actor depends on
        self._actor_dependents = {
            actor_config.name: set() for actor_config in actor_configs
        }  # Actors that depend on this actor
        for actor_config in actor_configs:
            dependencies = self.actors[actor_config.name]._actor.dependencies
            for dependency in dependencies:
                for actor in actor_configs:
                    if dependency == actor.template_key and dependency != actor_config.template_key:
                        self._actor_dependencies[actor_config.name].add(
                            actor.name,
                        )
                        self._actor_dependents[actor.name].add(
                            actor_config.name,
                        )
                    elif (
                        not dependency.startswith("_inputs[")
                        and not dependency == "processor"
                        and actor.template_key == ""
                    ):
                        self._actor_dependencies[actor_config.name].add(
                            actor.name,
                        )
                        self._actor_dependents[actor.name].add(
                            actor_config.name,
                        )

        # Set a timer for TIMEOUT seconds to stop the coordinator when there is
        # no activity
        self._idle_timer = ResettableTimer(TIMEOUT, self.on_timer_expire)
        self._idle_timer.start()

        for actor in self._actor_dependencies:
            if not self._actor_dependencies[actor] and actor not in [
                "input",
                "output",
                "bookkeeping",
            ]:
                logger.info(
                    f"Actor {actor} has no dependencies. Sending BEGIN message",
                )
                self.actors[actor].tell(
                    Message(message_type=MessageType.BEGIN),
                )

    def relay(self, message: Message):
        self._idle_timer.reset()

        # Collect stream errors
        if message.message_type == MessageType.STREAM_ERROR:
            self._stream_errors[message.message_from] = message.message

        # If bookkeeping is done, we can stop the coordinator
        if message.message_type == MessageType.BOOKKEEPING_DONE:
            self.force_stop()
            return

        logger.debug(
            f"Relaying message {message} to {self._actor_dependents.get(message.message_from)}",
        )

        # If it is a targetted message, send it to the targetted actor
        if message.message_to and message.message_to in self.actors:
            logger.info(
                f"Sending message {message} to {message.message_to} from {message.message_from}",
            )
            self.actors[message.message_to].tell(message)
            return

        from_actor_config = self._actor_configs.get(message.message_from)
        message.template_key = from_actor_config.template_key
        # Find actors that are dependent on the incoming stream and send the
        # message to them
        for actor_name in self._actor_dependents.get(message.message_from, []):
            self.actors[actor_name].tell(message)

    def get_actor(self, name):
        return self.actors[name]

    def on_timer_expire(self) -> None:
        logger.info(f"Coordinator {self.actor_urn} timed out")
        output_actor_ref = self.actors.get("output")
        if output_actor_ref:
            if len(self._stream_errors.keys()) > 0:
                # We timed out because some actor in the chain errored out
                errors = list(
                    map(lambda x: self._stream_errors[x], self._stream_errors),
                )
                output_actor_ref.tell(
                    Message(
                        message_type=MessageType.STREAM_ERROR,
                        message={
                            "errors": errors,
                        },
                    ),
                )
            else:
                output_actor_ref.tell(
                    Message(
                        message_type=MessageType.STREAM_ERROR,
                        message={
                            "errors": ["Timed out waiting for response"],
                        },
                    ),
                )
            ResettableTimer(10, self.force_stop).start()

    def on_stop(self) -> None:
        logger.info(f"Coordinator {self.actor_urn} stopping")
        self._idle_timer.stop()
        for actor in self.actors.values():
            try:
                actor.stop(block=False)
            except ActorDeadError:
                pass
            except Exception as e:
                logger.error(f"Failed to stop actor {actor}: {e}")

    def force_stop(self) -> None:
        try:
            self.stop()
        except ActorDeadError:
            pass
        except Exception as e:
            logger.error(f"Failed to stop coordinator {self}: {e}")
