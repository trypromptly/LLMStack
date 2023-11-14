import asyncio
import logging
import orjson as json

from llmstack.apps.handlers.app_runnner import AppRunner
from llmstack.play.actor import ActorConfig
from llmstack.play.actors.bookkeeping import BookKeepingActor
from llmstack.play.actors.input import InputActor
from llmstack.play.actors.output import OutputActor
from llmstack.play.actors.agent import AgentActor
from llmstack.play.coordinator import Coordinator
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface
from llmstack.processors.providers.promptly.http_api import PromptlyHttpAPIProcessor

logger = logging.getLogger(__name__)


class AgentRunner(AppRunner):
    def _get_processors_as_functions(self):
        functions = []
        processor_classes = {}

        for processor_class in ApiProcessorInterface.__subclasses__():
            processor_classes[(processor_class.provider_slug(),
                               processor_class.slug())] = processor_class

        for processor in self.app_data['processors'] if self.app_data and 'processors' in self.app_data else []:
            if (processor['provider_slug'], processor['processor_slug']) not in processor_classes:
                continue
            functions.append({
                'name': processor['id'],
                'description': processor['description'],
                'parameters': processor_classes[(processor['provider_slug'], processor['processor_slug'])].get_tool_input_schema(processor),
            })
        return functions

    def run_app(self):
        # Check if the app access permissions are valid
        self._is_app_accessible()

        csp = 'frame-ancestors self'
        if self.app.is_published:
            csp = 'frame-ancestors *'
            if self.web_config and 'allowed_sites' in self.web_config and len(self.web_config['allowed_sites']) > 0:
                csp = 'frame-ancestors ' + \
                    ' '.join(self.web_config['allowed_sites'])

        processor_actor_configs, processor_configs = self._get_processor_actor_configs()
        # Actor configs
        actor_configs = [
            ActorConfig(
                name='input', template_key='_inputs0', actor=InputActor, kwargs={'input_request': self.input_actor_request},
            ),
            ActorConfig(
                name='agent', template_key='agent', actor=AgentActor, kwargs={'processor_configs': processor_configs, 'functions': self._get_processors_as_functions(), 'input': self.request.data.get('input', {}), 'env': self.app_owner_profile.get_vendor_env(), 'config': self.app_data['config']}
            ),
            ActorConfig(
                name='output', template_key='output',
                dependencies=['_inputs0', 'agent'],
                actor=OutputActor, kwargs={
                    'template': self.app_data['output_template']['markdown']}
            ),
        ]

        actor_configs.extend(map(lambda x: ActorConfig(
            name=x.name, template_key=x.template_key, actor=x.actor, dependencies=(x.dependencies + ['agent']), kwargs=x.kwargs), processor_actor_configs)
        )
        actor_configs.append(
            ActorConfig(
                name='bookkeeping', template_key='bookkeeping', actor=BookKeepingActor, dependencies=['_inputs0', 'output', 'agent'], kwargs={'processor_configs': processor_configs, 'is_agent': True},
            ),
        )

        try:
            coordinator_ref = Coordinator.start(
                session_id=self.app_session['uuid'], actor_configs=actor_configs,
            )
            coordinator = coordinator_ref.proxy()

            agent_actor = coordinator.get_actor('agent').get().proxy()
            agent_actor.run()

            output = None
            input_actor = coordinator.get_actor('input').get().proxy()
            output_actor = coordinator.get_actor('output').get().proxy()
            output_iter = None
            if input_actor and output_actor:
                input_actor.write(self.request.data.get('input', {})).get()
                output_iter = output_actor.get_output().get(
                ) if not self.stream else output_actor.get_output_stream().get()

            if self.stream:
                # Return a wrapper over output_iter where we call next() on output_iter and yield the result
                async def stream_output():
                    metadata_sent = False
                    try:
                        while True:
                            await asyncio.sleep(0.0001)
                            if not metadata_sent:
                                metadata_sent = True
                                yield {'session': {'id': self.app_session['uuid']}, 'csp': csp, 'templates': {**{k: v['processor']['output_template'] for k, v in processor_configs.items()}, **{'agent': self.app_data['output_template']}} if processor_configs else {'agent': self.app_data['output_template']}}
                            output = next(output_iter)
                            yield output
                    except StopIteration:
                        pass
                    except Exception as e:
                        logger.exception(e)
                        coordinator_ref.stop()
                        raise Exception(f'Error streaming output: {e}')
                return stream_output()

            for output in output_iter:
                # Iterate through output_iter to get the final output
                pass

        except Exception as e:
            logger.exception(e)
            raise Exception(f'Error starting coordinator: {e}')

        return {
            'session': {'id': self.app_session['uuid']},
            'output': output, 'csp': csp,
        }
