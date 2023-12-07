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

logger = logging.getLogger(__name__)


class AgentRunner(AppRunner):
    pass