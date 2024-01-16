import asyncio
import logging
import uuid

from rest_framework.request import Request

from llmstack.apps.app_session_utils import create_agent_app_session_data, create_app_session, get_agent_app_session_data
from llmstack.apps.app_session_utils import create_app_session_data
from llmstack.apps.app_session_utils import get_app_session
from llmstack.apps.app_session_utils import get_app_session_data
from llmstack.apps.integration_configs import WebIntegrationConfig
from llmstack.apps.models import AppVisibility
from llmstack.play.actor import ActorConfig
from llmstack.play.actors.agent import AgentActor
from llmstack.play.actors.bookkeeping import BookKeepingActor
from llmstack.play.actors.input import InputActor, InputRequest
from llmstack.play.actors.output import OutputActor
from llmstack.play.coordinator import Coordinator
from llmstack.play.utils import convert_template_vars_from_legacy_format
from llmstack.base.models import Profile
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface
from llmstack.processors.providers.api_processors import ApiProcessorFactory

logger = logging.getLogger(__name__)


class AppRunner:
    def __init__(
            self,
            app,
            app_data,
            request_uuid,
            request: Request,
            app_owner,
            session_id=None,
            stream=False,
            request_ip='',
            request_location='',
            request_user_agent='',
            request_content_type=''):
        self.app = app
        self.app_data = app_data
        self.app_owner_profile = app_owner
        self.request = request
        self.app_run_request_user = request.user
        self.session_id = session_id
        self.app_session = self._get_or_create_app_session()

        self.stream = stream

        self.web_config = WebIntegrationConfig().from_dict(
            app.web_integration_config,
            app_owner.decrypt_value,
        ) if app.web_integration_config else None

        self.app_init()

        request_user_email = ''
        if not self.app_run_request_user.is_anonymous:
            if self.app_run_request_user and self.app_run_request_user.email and len(
                    self.app_run_request_user.email) > 0:
                request_user_email = self.app_run_request_user.email
            elif self.app_run_request_user and self.app_run_request_user.username and len(self.app_run_request_user.username) > 0:
                request_user_email = self.app_run_request_user.username

        self.input_actor_request = InputRequest(
            request_app_uuid=self.app.uuid,
            request_endpoint_uuid='',
            request_app_session_key=self.session_id,
            request_owner=self.app_owner_profile.user,
            request_uuid=request_uuid,
            request_user_email=request_user_email,
            request_ip=request_ip,
            request_location=request_location,
            request_user_agent=request_user_agent,
            request_content_type=request_content_type,
            request_body=request.data,
        )

    def app_init(self):
        """
        App specific state initialization
        """
        pass

    def _get_or_create_app_session(self):
        app_session = None
        if not self.session_id:
            self.session_id = str(uuid.uuid4())

        app_session = get_app_session(
            self.session_id,
        ) or create_app_session(self.app, self.session_id)

        return app_session

    def _is_app_accessible(self):
        # Return 404 if the app is not published. If the app is published but
        # not public, return 404 for non owner
        if not self.app.is_published and self.app.owner != self.app_run_request_user:
            raise Exception('App not found')

        if self.app.visibility == AppVisibility.ORGANIZATION and self.app_owner_profile.organization != Profile.objects.get(
                user=self.app_run_request_user).organization:
            raise Exception('App not found')

        if self.app.visibility == AppVisibility.PRIVATE and self.app_run_request_user != self.app.owner and self.app_run_request_user.email not in self.app.read_accessible_by and self.app_run_request_user.email not in self.app.write_accessible_by:
            raise Exception('App not found')

    def _get_processor_actor_configs(self):
        processor_actor_configs = []
        processor_configs = {}
        vendor_env = self.app_owner_profile.get_vendor_env()

        if self.app_data and 'processors' in self.app_data:
            processors = self.app_data['processors']

            # Create a list of actor configs for each processor
            for processor, index in zip(
                processors, range(
                    1, len(processors) + 1)):
                if 'processor_slug' not in processor or 'provider_slug' not in processor:
                    raise Exception(
                        'processor_slug and provider_slug are required for each processor')

                processor_cls = ApiProcessorFactory.get_api_processor(
                    processor['processor_slug'], processor['provider_slug'],
                )
                app_session_data = get_app_session_data(
                    self.app_session, processor,
                )
                if not app_session_data:
                    app_session_data = create_app_session_data(
                        self.app_session, processor, {},
                    )

                processor_actor_configs.append(
                    ActorConfig(
                        name=processor['id'],
                        template_key=f'_inputs{index}',
                        actor=processor_cls,
                        kwargs={
                            'id': processor['id'],
                            'env': vendor_env,
                            'input': convert_template_vars_from_legacy_format(
                                processor['input']),
                            'config': convert_template_vars_from_legacy_format(
                                processor['config']),
                            'session_data': app_session_data['data'] if app_session_data and 'data' in app_session_data else {},
                            'is_tool': True if self.app.type.slug == 'agent' else False,
                        },
                        output_cls=processor_cls.get_output_cls(),
                    ),
                )
                processor_configs[processor['id']] = {
                    'app_session': self.app_session,
                    'app_session_data': app_session_data,
                    'processor': processor,
                    'template_key': f'_inputs{index}',
                }
        else:
            # Get all processors from run_graph and remove empty ones
            processors = [
                x.exit_endpoint for x in self.app.run_graph.all().order_by(
                    'id',
                ) if x is not None and x.exit_endpoint is not None
            ]

            # Create a list of actor configs for each processor
            for processor, index in zip(
                processors, range(
                    1, len(processors) + 1)):
                processor_cls = ApiProcessorFactory.get_api_processor(
                    processor.api_backend.slug, processor.api_backend.api_provider.slug, )
                app_session_data = get_app_session_data(
                    self.app_session, processor,
                )
                if not app_session_data:
                    app_session_data = create_app_session_data(
                        self.app_session, processor, {},
                    )

                processor_actor_configs.append(
                    ActorConfig(
                        name=str(
                            processor.uuid),
                        template_key=f'_inputs{index}',
                        actor=processor_cls,
                        kwargs={
                            'env': vendor_env,
                            'input': convert_template_vars_from_legacy_format(
                                processor.input),
                            'config': convert_template_vars_from_legacy_format(
                                processor.config),
                            'session_data': app_session_data['data'] if app_session_data and 'data' in app_session_data else {},
                        },
                        output_cls=processor_cls.get_output_cls(),
                    ),
                )
                processor_configs[str(processor.uuid)] = {
                    'app_session': self.app_session,
                    'app_session_data': app_session_data,
                    'processor': processor,
                    'template_key': f'_inputs{index}',
                }
        return processor_actor_configs, processor_configs

    def _get_processors_as_functions(self):
        functions = []
        processor_classes = {}

        for processor_class in ApiProcessorInterface.__subclasses__():
            processor_classes[(processor_class.provider_slug(),
                               processor_class.slug())] = processor_class

        for processor in self.app_data['processors'] if self.app_data and 'processors' in self.app_data else [
        ]:
            if (processor['provider_slug'],
                    processor['processor_slug']) not in processor_classes:
                continue
            functions.append({'name': processor['id'], 'description': processor['description'], 'parameters': processor_classes[(
                processor['provider_slug'], processor['processor_slug'])].get_tool_input_schema(processor), })
        return functions

    def _start(
            self,
            input_data,
            app_session,
            actor_configs,
            csp,
            template,
            processor_configs=[]):
        try:
            coordinator_ref = Coordinator.start(
                session_id=app_session['uuid'], actor_configs=actor_configs,
            )
            coordinator = coordinator_ref.proxy()

            output = None
            input_actor = coordinator.get_actor('input').get().proxy()
            output_actor = coordinator.get_actor('output').get().proxy()
            output_iter = None
            if input_actor and output_actor:
                input_actor.write(input_data.get('input', {})).get()
                output_iter = output_actor.get_output().get(
                ) if not self.stream else output_actor.get_output_stream().get()

            if self.stream:
                # Return a wrapper over output_iter where we call next() on
                # output_iter and yield the result
                async def stream_output():
                    metadata_sent = False
                    try:
                        while True:
                            await asyncio.sleep(0.0001)
                            if not metadata_sent:
                                metadata_sent = True
                                yield {'session': {'id': app_session['uuid']}, 'csp': csp, 'template': template}
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

    def _start_agent(
            self,
            input_data,
            app_session,
            actor_configs,
            csp,
            template,
            processor_configs=[]):
        try:
            coordinator_ref = Coordinator.start(
                session_id=self.app_session['uuid'], actor_configs=actor_configs, )
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
                # Return a wrapper over output_iter where we call next() on
                # output_iter and yield the result
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

    def _get_csp(self):
        csp = 'frame-ancestors self'
        if self.app.is_published:
            csp = 'frame-ancestors *'
            if self.web_config and 'allowed_sites' in self.web_config and len(
                    self.web_config['allowed_sites']) > 0:
                csp = 'frame-ancestors ' + \
                    ' '.join(self.web_config['allowed_sites'])
        return csp

    def _get_base_actor_configs(self, output_template, processor_configs):
        actor_configs = []
        if self.app.type.slug == 'agent':
            agent_app_session_data = get_agent_app_session_data(
                self.app_session)
            if not agent_app_session_data:
                agent_app_session_data = create_agent_app_session_data(
                    self.app_session, {})

            actor_configs = [
                ActorConfig(
                    name='input',
                    template_key='_inputs0',
                    actor=InputActor,
                    kwargs={
                        'input_request': self.input_actor_request},
                ),
                ActorConfig(
                    name='agent',
                    template_key='agent',
                    actor=AgentActor,
                    kwargs={
                        'processor_configs': processor_configs,
                        'functions': self._get_processors_as_functions(),
                        'input': self._get_input_data().get(
                            'input',
                            {}),
                        'env': self.app_owner_profile.get_vendor_env(),
                        'config': self.app_data['config'],
                        'agent_app_session_data': agent_app_session_data,
                    }),
                ActorConfig(
                    name='output',
                    template_key='output',
                    dependencies=[
                        '_inputs0',
                        'agent'],
                    actor=OutputActor,
                    kwargs={
                        'template': self.app_data['output_template']['markdown']}),
            ]
        else:
            # Actor configs
            actor_configs = [
                ActorConfig(
                    name='input', template_key='_inputs0', actor=InputActor, kwargs={
                        'input_request': self.input_actor_request}, ), ActorConfig(
                    name='output', template_key='output', actor=OutputActor, kwargs={
                        'template': output_template}, ), ]
        return actor_configs

    def _get_bookkeeping_actor_config(self, processor_configs):
        if self.app.type.slug == 'agent':
            return ActorConfig(
                name='bookkeeping',
                template_key='bookkeeping',
                actor=BookKeepingActor,
                dependencies=[
                    '_inputs0',
                    'output',
                    'agent'],
                kwargs={
                    'processor_configs': processor_configs,
                    'is_agent': True},
            )
        else:
            return ActorConfig(
                name='bookkeeping', template_key='bookkeeping',
                actor=BookKeepingActor, dependencies=['_inputs0', 'output'],
                kwargs={'processor_configs': processor_configs},
            )

    def _get_input_data(self):
        input = self.request.data.get('input', {})
        return {'input': {**input, "_request": {}}}

    def _get_actor_configs(
            self,
            template,
            processor_configs,
            processor_actor_configs):
        # Actor configs
        actor_configs = self._get_base_actor_configs(
            template, processor_configs)

        if self.app.type.slug == 'agent':
            actor_configs.extend(
                map(
                    lambda x: ActorConfig(
                        name=x.name,
                        template_key=x.template_key,
                        actor=x.actor,
                        dependencies=(
                            x.dependencies +
                            ['agent']),
                        kwargs=x.kwargs),
                    processor_actor_configs))
        else:
            actor_configs.extend(processor_actor_configs)

        actor_configs.append(
            self._get_bookkeeping_actor_config(processor_configs))

        return actor_configs

    def run_app(self):
        # Check if the app access permissions are valid
        self._is_app_accessible()

        csp = self._get_csp()

        template = convert_template_vars_from_legacy_format(
            self.app_data['output_template'].get(
                'markdown',
                '') if self.app_data and 'output_template' in self.app_data else self.app.output_template.get(
                'markdown',
                ''),
        )
        processor_actor_configs, processor_configs = self._get_processor_actor_configs()
        actor_configs = self._get_actor_configs(
            template, processor_configs, processor_actor_configs)

        if self.app.type.slug == 'agent':
            return self._start_agent(
                self._get_input_data(), self.app_session,
                actor_configs, csp, template,
                processor_configs)
        else:
            return self._start(
                self._get_input_data(), self.app_session,
                actor_configs, csp, template,
            )
