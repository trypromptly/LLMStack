import asyncio
import logging
import orjson as json
from llmstack.apps.app_session_utils import create_agent_app_session_data, get_agent_app_session_data

from llmstack.apps.handlers.app_runnner import AppRunner
from llmstack.play.actor import ActorConfig
from llmstack.play.actors.bookkeeping import BookKeepingActor
from llmstack.play.actors.input import InputActor
from llmstack.play.actors.output import OutputActor
from llmstack.play.actors.agent import AgentActor
from llmstack.play.coordinator import Coordinator
from llmstack.play.utils import convert_template_vars_from_legacy_format
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface
from llmstack.processors.providers.promptly.http_api import PromptlyHttpAPIProcessor

logger = logging.getLogger(__name__)


class AgentRunner(AppRunner):
    
    def _get_base_actor_configs(self, output_template, processor_configs):
        agent_app_session_data = get_agent_app_session_data(self.app_session)
        if not agent_app_session_data:
            agent_app_session_data = create_agent_app_session_data(self.app_session, {})
            
        actor_configs = [
            ActorConfig(
                name='input', template_key='_inputs0', actor=InputActor, kwargs={'input_request': self.input_actor_request},
            ),
            ActorConfig(
                name='agent', template_key='agent', 
                actor=AgentActor, 
                kwargs={
                        'processor_configs': processor_configs, 
                        'functions': self._get_processors_as_functions(), 
                        'input': self.request.data.get('input', {}), 'env': self.app_owner_profile.get_vendor_env(), 
                        'config': self.app_data['config'],
                        'agent_app_session_data': agent_app_session_data,
                        }
            ),
            ActorConfig(
                name='output', template_key='output',
                dependencies=['_inputs0', 'agent'],
                actor=OutputActor, kwargs={
                    'template': self.app_data['output_template']['markdown']}
            ),
        ] 
        return actor_configs
    
    def _start(self, input_data, app_session, actor_configs, csp, template, processor_configs=[]):
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
                input_actor.write(input_data.get('input', {})).get()
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

    def _get_bookkeeping_actor_config(self, processor_configs):
        return ActorConfig(
                name='bookkeeping', template_key='bookkeeping', 
                actor=BookKeepingActor,
                dependencies=['_inputs0', 'output', 'agent'], 
                kwargs={'processor_configs': processor_configs, 'is_agent': True},
            )
        
    def run_app(self):
        # Check if the app access permissions are valid
        self._is_app_accessible()

        csp = self._get_csp()

        processor_actor_configs, processor_configs = self._get_processor_actor_configs()
        
        template = convert_template_vars_from_legacy_format(
            self.app_data['output_template'].get(
                'markdown', '') if self.app_data and 'output_template' in self.app_data else self.app.output_template.get('markdown', ''),
        )
            
        # Actor configs
        actor_configs = self._get_base_actor_configs(template, processor_configs)

        actor_configs.extend(map(lambda x: ActorConfig(
            name=x.name, template_key=x.template_key, actor=x.actor, dependencies=(x.dependencies + ['agent']), kwargs=x.kwargs), processor_actor_configs)
        )
        actor_configs.append(self._get_bookkeeping_actor_config(processor_configs))
        
        input_data = self.request.data
        return self._start(
            input_data, self.app_session,
            actor_configs, csp, template,
            processor_configs)