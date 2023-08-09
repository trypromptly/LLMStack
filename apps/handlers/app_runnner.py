import asyncio
import json
import logging
import uuid

from rest_framework.request import Request

from apps.app_session_utils import create_app_session
from apps.app_session_utils import create_app_session_data
from apps.app_session_utils import get_app_session
from apps.app_session_utils import get_app_session_data
from apps.integration_configs import DiscordIntegrationConfig
from apps.integration_configs import SlackIntegrationConfig
from apps.integration_configs import WebIntegrationConfig
from apps.models import AppVisibility
from common.utils.utils import get_location
from play.actor import ActorConfig
from play.actors.bookkeeping import BookKeepingActor
from play.actors.input import InputActor
from play.actors.input import InputRequest
from play.actors.output import OutputActor
from play.coordinator import Coordinator
from play.utils import convert_template_vars_from_legacy_format
from base.models import Profile
from processors.providers.api_processors import ApiProcessorFactory

logger = logging.getLogger(__name__)


class AppRunner:
    def __init__(self, app, request_uuid, request: Request, app_owner, session_id=None):
        self.app = app
        self.stream = request.data.get('stream', False)
        self.app_owner_profile = app_owner
        self.request = request
        self.app_run_request_user = request.user
        self.session_id = session_id
        self.app_session = self._get_or_create_app_session()
        self.web_config = WebIntegrationConfig().from_dict(
            app.web_integration_config,
            app_owner.decrypt_value,
        ) if app.web_integration_config else None
        self.slack_config = SlackIntegrationConfig().from_dict(
            app.slack_integration_config,
            app_owner.decrypt_value,
        ) if app.slack_integration_config else None
        self.discord_config = DiscordIntegrationConfig().from_dict(
            app.discord_integration_config,
            app_owner.decrypt_value,
        ) if app.discord_integration_config else None

        self.app_init()

        request_user_email = ''
        if self.app_run_request_user and not self.app_run_request_user.is_anonymous:
            request_user_email = self.app_run_request_user.email

        request_ip = request.headers.get(
            'X-Forwarded-For', request.META.get(
                'REMOTE_ADDR', '',
            ),
        ).split(',')[0].strip() or request.META.get('HTTP_X_REAL_IP', '')
        request_location = request.headers.get('X-Client-Geo-Location', '')

        if not request_location:
            location = get_location(request_ip)
            request_location = f"{location.get('city', '')}, {location.get('country_code', '')}" if location else ''

        self.input_actor_request = InputRequest(
            request_app_uuid=self.app.uuid,
            request_endpoint_uuid='',
            request_app_session_key=self.session_id,
            request_owner=self.app_owner_profile.user,
            request_uuid=request_uuid,
            request_user_email=request_user_email,
            request_ip=request_ip,
            request_location=request_location,
            request_user_agent=request.META.get('HTTP_USER_AGENT', ''),
            request_content_type=request.META.get('CONTENT_TYPE', ''),
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
        # Return 404 if the app is not published. If the app is published but not public, return 404 for non owner
        if not self.app.is_published and self.app.owner != self.app_run_request_user:
            raise Exception('App not found')

        if self.app.visibility == AppVisibility.ORGANIZATION and self.app_owner_profile.organization != Profile.objects.get(user=self.app_run_request_user).organization:
            raise Exception('App not found')

        if self.app.visibility == AppVisibility.PRIVATE and self.app_run_request_user != self.app.owner and self.app_run_request_user.email not in self.app.accessible_by:
            raise Exception('App not found')

    def _get_processor_actor_configs(self):
        # Get all processors from run_graph and remove empty ones
        processors = [
            x.exit_endpoint for x in self.app.run_graph.all().order_by(
                'id',
            ) if x is not None and x.exit_endpoint is not None
        ]
        vendor_env = self.app_owner_profile.get_vendor_env()
        processor_configs = {}

        processor_actor_configs = []
        # Create a list of actor configs for each processor
        for processor, index in zip(processors, range(1, len(processors)+1)):
            processor_cls = ApiProcessorFactory.get_api_processor(
                processor.api_backend.slug,
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
                    name=str(processor.uuid), template_key=f'_inputs{index}', actor=processor_cls, kwargs={
                        'env': vendor_env,
                        'input': convert_template_vars_from_legacy_format(processor.input),
                        'config': convert_template_vars_from_legacy_format(processor.config),
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

    def _start(self, input_data, app_session, actor_configs, csp, template):
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
                # Return a wrapper over output_iter where we call next() on output_iter and yield the result
                async def stream_output():
                    metadata_sent = False
                    try:
                        while True:
                            await asyncio.sleep(0.0001)
                            if not metadata_sent:
                                metadata_sent = True
                                yield json.dumps({'session': {'id': app_session['uuid']}, 'csp': csp, 'template': template}) + '\n'
                            output = next(output_iter)
                            yield json.dumps(output) + '\n'
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

    def run_app(self):
        # Check if the app access permissions are valid
        self._is_app_accessible()

        template = convert_template_vars_from_legacy_format(
            self.app.output_template.get('markdown', ''),
        )

        debug_data = []

        csp = 'frame-ancestors self'
        if self.app.is_published:
            csp = 'frame-ancestors *'
            if self.web_config and 'allowed_sites' in self.web_config and len(self.web_config['allowed_sites']) > 0:
                csp = 'frame-ancestors ' + \
                    ' '.join(self.web_config['allowed_sites'])

        # Actor configs
        actor_configs = [
            ActorConfig(
                name='input', template_key='_inputs0', actor=InputActor, kwargs={'input_request': self.input_actor_request},
            ),
            ActorConfig(
                name='output', template_key='output',
                actor=OutputActor, kwargs={'template': template},
            ),
        ]
        processor_actor_configs, processor_configs = self._get_processor_actor_configs()
        actor_configs.extend(processor_actor_configs)
        actor_configs.append(
            ActorConfig(
                name='bookkeeping', template_key='bookkeeping', actor=BookKeepingActor, dependencies=['_inputs0', 'output'], kwargs={'processor_configs': processor_configs},
            ),
        )

        input_data = self.request.data
        return self._start(
            input_data, self.app_session,
            actor_configs, csp, template,
        )
