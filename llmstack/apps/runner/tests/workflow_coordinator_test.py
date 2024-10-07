import asyncio
import logging
import time
import unittest

from llmstack.apps.runner.workflow_coordinator import WorkflowCoordinator
from llmstack.play.actor import ActorConfig
from llmstack.processors.providers.promptly.echo import EchoProcessor

# Set up logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TestWorkflowCoordinator(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.mock_actor = EchoProcessor
        self.mock_kwargs = {
            "input": {
                "input_str": "Hello, World!",
                "stream": False,
            },
            "config": {},
            "env": {},
        }
        self.mock_actor_config = ActorConfig(
            name="test_actor",
            actor=self.mock_actor,
            dependencies=[],
            kwargs=self.mock_kwargs,
        )

    def tearDown(self):
        time.sleep(0.2)
        self.coordinator.stop()
        self.loop.close()

    def test_init_empty_actor_configs(self):
        self.coordinator = WorkflowCoordinator.start([]).proxy()
        self.assertEqual(self.coordinator.get_dependencies_map().get(), {"input": set(), "output": {"input"}})
        self.assertEqual(self.coordinator.get_dependents_map().get(), {"input": {"output"}, "output": set()})

    def test_init_single_actor_no_dependencies(self):
        self.coordinator = WorkflowCoordinator.start([self.mock_actor_config]).proxy()
        self.assertEqual(
            self.coordinator.get_dependencies_map().get(),
            {"input": set(), "output": {"input", "test_actor"}, "test_actor": set()},
        )
        self.assertEqual(
            self.coordinator.get_dependents_map().get(),
            {"input": {"output", "test_actor"}, "output": set(), "test_actor": {"output"}},
        )

    def test_init_multiple_actors_with_dependencies(self):
        actor1 = ActorConfig(name="actor1", actor=self.mock_actor, dependencies=[], kwargs=self.mock_kwargs)
        actor2 = ActorConfig(name="actor2", actor=self.mock_actor, dependencies=["actor1"], kwargs=self.mock_kwargs)
        actor3 = ActorConfig(
            name="actor3", actor=self.mock_actor, dependencies=["actor1", "actor2"], kwargs=self.mock_kwargs
        )

        self.coordinator = WorkflowCoordinator.start([actor1, actor2, actor3]).proxy()

        self.assertEqual(
            self.coordinator.get_dependencies_map().get(),
            {
                "input": set(),
                "actor1": set(),
                "actor2": {"actor1"},
                "actor3": {"actor1", "actor2"},
                "output": {"input", "actor1", "actor2", "actor3"},
            },
        )
        self.assertEqual(
            self.coordinator.get_dependents_map().get(),
            {
                "input": {"output", "actor1", "actor2", "actor3"},
                "actor1": {"actor2", "actor3", "output"},
                "actor2": {"actor3", "output"},
                "actor3": {"output"},
                "output": set(),
            },
        )

    def test_input_output_without_actors(self):
        self.coordinator = WorkflowCoordinator.start(actor_configs=[], output_template="{{input.data}}").proxy()
        self.coordinator.input({"data": "Hello, World!"}).get()

        self.assertEqual(list(self.coordinator.output().get())[0]["output"], "Hello, World!")

    def test_input_output_with_actors(self):
        self.coordinator = WorkflowCoordinator.start(
            actor_configs=[self.mock_actor_config], output_template="{{test_actor.output_str}} {{input.data}}"
        ).proxy()
        self.coordinator.input({"data": "New!"}).get()

        self.assertEqual(list(self.coordinator.output().get())[0]["output"], "Hello, World! New!")


if __name__ == "__main__":
    unittest.main()
