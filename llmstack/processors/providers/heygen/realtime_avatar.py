import json
import logging
from enum import Enum
from typing import List, Optional

from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.common.utils.prequests import post
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    CREATE_SESSION = 'create_session'
    START_SESSION = 'start_session'
    SUBMIT_ICE_CANDIDATE = 'submit_ice_candidate'
    CLOSE_SESSION = 'close_session'
    REPEAT = 'repeat'
    TALK = 'talk'

    def __str__(self):
        return self.value


class RealtimeAvatarInput(ApiProcessorSchema):
    task_type: TaskType = Field(
        description='The type of the task.', default=TaskType.REPEAT)
    text: Optional[str] = Field(
        description='The text of the task.', widget='textarea')
    session_id: Optional[str] = Field(
        description='The session ID to use.', default=None)


class RealtimeAvatarOutput(ApiProcessorSchema):
    task_type: TaskType = Field(
        description='The type of the task.', default=TaskType.REPEAT)
    task_response_json: str = Field(description='The response of the task.')


class Quality(str, Enum):
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'

    def __str__(self):
        return self.value


class RealtimeAvatarConfiguration(ApiProcessorSchema):
    quality: Optional[Quality] = Field(
        description='The quality of the data to be retrieved.', default=Quality.HIGH)
    avatar_name: Optional[str] = Field(
        description='The name of the avatar to be used.', default='default')
    voice_id: Optional[str] = Field(
        description='Voice to use. selected from voice list')

    sdp_type: Optional[str] = Field(
        description='SDP type', default=None)
    sdp: Optional[str] = Field(
        description='SDP', default=None)

    candidate: Optional[str] = Field(
        description='ICE candidate', default=None)
    sdp_mid: Optional[str] = Field(
        description='The media stream identification for the ICE candidate.', default=None)
    sdp_mline_index: Optional[int] = Field(
        description='The index (starting at 0) of the m-line in the SDP.', default=None)
    username_fragment: Optional[str] = Field(
        description='The username fragment for the ICE candidate.', default=None)

    connection_id: Optional[str] = Field(
        widget='connection',  advanced_parameter=False, description='Use your authenticated connection to make the request')


class RealtimeAvatarProcessor(ApiProcessorInterface[RealtimeAvatarInput, RealtimeAvatarOutput, RealtimeAvatarConfiguration]):
    @staticmethod
    def name() -> str:
        return 'Realtime Avatar'

    @staticmethod
    def slug() -> str:
        return 'realtime_avatar'

    @staticmethod
    def description() -> str:
        return 'Bring digital avatars to life in real time.'

    @staticmethod
    def provider_slug() -> str:
        return 'heygen'

    def process(self) -> dict:
        output_stream = self._output_stream

        session_id = self._input.session_id
        task_type = self._input.task_type.strip().lower().rstrip()

        connection = self._env['connections'].get(
            self._config.connection_id, None) if self._config.connection_id else None

        if connection is None:
            raise Exception('Connection not found')

        if task_type == TaskType.CREATE_SESSION:
            logger.info('Creating session')
            create_session_url = 'https://api.heygen.com/v1/realtime.new'
            body = {
                'quality': self._config.quality.value,
                'avatar_name': self._config.avatar_name,
                'voice': {
                    'voice_id': self._config.voice_id
                }
            }
            response = post(create_session_url, json=body,
                            _connection=connection)
            if response.status_code != 200:
                logger.error(f'Error creating session: {response.text}')
                raise Exception('Error creating session')

            result = RealtimeAvatarOutput(
                task_type=task_type,
                task_response_json=json.dumps(response.json()),
            )

        elif task_type == TaskType.START_SESSION:
            start_session_url = 'https://api.heygen.com/v1/realtime.start'
            body = {
                "session_id": session_id,
                "sdp": {
                    "type": self._config.sdp_type,
                    "sdp": self._config.sdp
                }
            }
            response = post(start_session_url, json=body,
                            _connection=connection)

            if response.status_code != 200:
                logger.error(f'Error starting session: {response.text}')
                raise Exception('Error starting session')

            result = RealtimeAvatarOutput(
                task_type=task_type,
                task_response_json=json.dumps(response.json()),
            )

        elif task_type == TaskType.SUBMIT_ICE_CANDIDATE:
            result = RealtimeAvatarOutput(
                task_type=task_type,
                task_response_json=json.dumps({}),
            )
        elif task_type == TaskType.CLOSE_SESSION:
            result = RealtimeAvatarOutput(
                task_type=task_type,
                task_response_json=json.dumps({}),
            )
        elif task_type == TaskType.REPEAT or task_type == TaskType.TALK:
            task_url = 'https://api.heygen.com/v1/realtime.task'
            body = {
                "session_id": session_id,
                "text": self._input.text,
                "task_type": task_type
            }
            response = post(task_url, json=body, _connection=connection)
            if response.status_code != 200:
                logger.error(f'Error creating task: {response.text}')
                raise Exception('Error creating task')

            result = RealtimeAvatarOutput(
                task_type=task_type,
                task_response_json=json.dumps(response.json()),
            )

        async_to_sync(output_stream.write)(result)

        return output_stream.finalize()
