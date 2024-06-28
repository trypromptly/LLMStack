import logging
import time
from enum import Enum
from typing import Any, Dict, Optional

from asgiref.sync import async_to_sync
from pydantic import Field, model_validator

from llmstack.common.utils.prequests import post
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
    hydrate_input,
)

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    CREATE_SESSION = "create_session"
    START_SESSION = "start_session"
    SUBMIT_ICE_CANDIDATE = "submit_ice_candidate"
    CLOSE_SESSION = "close_session"
    REPEAT = "repeat"
    TALK = "talk"

    def __str__(self):
        return self.value


class RealtimeAvatarInput(ApiProcessorSchema):
    task_type: TaskType = Field(
        description="The type of the task. Only valid selections are repeat and talk",
        default=TaskType.REPEAT,
    )
    task_input_json: Optional[Dict] = Field(
        description="The input of the task.",
        default=None,
        json_schema_extra={"widget": "hidden"},
    )
    text: Optional[str] = Field(description="The text of the task.")
    session_id: Optional[str] = Field(
        description="The session ID to use.",
        default=None,
    )

    @model_validator(mode="before")
    def validate_input(cls, values):
        if (
            values.get("task_type") == TaskType.REPEAT
            or values.get(
                "task_type",
            )
            == TaskType.TALK
        ) and not values.get("text"):
            raise ValueError("Text is required for repeat/talk tasks")
        elif (
            values.get("task_type") is not TaskType.CREATE_SESSION
            and not values.get("task_input_json")
            and not values.get("text")
        ):
            raise ValueError("Task type is not supported")
        return values


class RealtimeAvatarOutput(ApiProcessorSchema):
    task_type: TaskType = Field(
        description="The type of the task.",
        default=TaskType.REPEAT,
    )
    task_response_json: Dict = Field(description="The response of the task.")


class Quality(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    def __str__(self):
        return self.value


class RealtimeAvatarConfiguration(ApiProcessorSchema):
    reuse_session: bool = Field(
        description="Reuse the heygen session if valid instesd of creating a new one.",
        default=False,
    )
    quality: Optional[Quality] = Field(
        description="The quality of the data to be retrieved.",
        default=Quality.MEDIUM,
    )
    avatar_name: Optional[str] = Field(
        description="The name of the avatar to be used.",
        json_schema_extra={"advanced_parameter": False},
    )
    voice_id: Optional[str] = Field(
        description="Voice to use. selected from voice list",
        json_schema_extra={"advanced_parameter": False},
    )

    connection_id: Optional[str] = Field(
        json_schema_extra={"advanced_parameter": False, "widget": "connection"},
        description="Use your authenticated connection to make the request",
    )

    input_stream: bool = Field(
        description="Process input as a stream, one sentence at a time.",
        default=False,
    )


class RealtimeAvatarProcessor(
    ApiProcessorInterface[RealtimeAvatarInput, RealtimeAvatarOutput, RealtimeAvatarConfiguration],
):
    def __init__(
        self,
        input,
        config,
        env,
        output_stream=None,
        dependencies=[],
        all_dependencies=[],
        metadata={},
        session_data=None,
        request=None,
        id=None,
        is_tool=False,
    ):
        super().__init__(
            input,
            config,
            env,
            output_stream,
            dependencies,
            all_dependencies,
            metadata,
            session_data,
            request,
            id,
            is_tool,
        )
        self._messages_to_repeat = []
        self._message_buffer = ""
        self._messages_repeated = 0

    @staticmethod
    def name() -> str:
        return "Realtime Avatar"

    @staticmethod
    def slug() -> str:
        return "realtime_avatar"

    @staticmethod
    def description() -> str:
        return "Bring digital avatars to life in real time."

    @staticmethod
    def provider_slug() -> str:
        return "heygen"

    def disable_history(self) -> bool:
        return self._disable_history

    def process_session_data(self, session_data):
        self._heygen_session = session_data.get("heygen_session", None)

    def session_data_to_persist(self) -> dict:
        session_data = {}
        if self._heygen_session:
            session_data["heygen_session"] = self._heygen_session

        return session_data

    def input_stream(self, message: Any) -> Any:
        if not self._config.input_stream:
            return

        input_data = (
            hydrate_input(
                self._input,
                message,
            )
            if message
            else self._input
        )

        session_id = (
            input_data.session_id
            if input_data.session_id
            else (self._heygen_session["data"]["session_id"] if self._heygen_session else None)
        )

        connection = (
            self._env["connections"].get(
                self._config.connection_id,
                None,
            )
            if self._config.connection_id
            else None
        )

        # Split self._input.text sentences into multiple messages
        if input_data.task_type == TaskType.TALK or input_data.task_type == TaskType.REPEAT:
            self._message_buffer += input_data.text
            self._messages_to_repeat = self._message_buffer.split(".")

            if len(self._messages_to_repeat) - 1 > self._messages_repeated:
                url = "https://api.heygen.com/v1/realtime.task"
                body = {
                    "session_id": session_id,
                    "text": self._messages_to_repeat[self._messages_repeated].strip(),
                }

                response = post(url, json=body, _connection=connection)
                self._messages_repeated += 1

                if response.status_code != 200:
                    logger.error(f"Error creating task for input stream: {response.text}")

    def process(self) -> dict:
        output_stream = self._output_stream
        self._disable_history = True

        session_id = (
            self._input.session_id
            if self._input.session_id
            else (self._heygen_session["data"]["session_id"] if self._heygen_session else None)
        )
        task_type = self._input.task_type
        url = None

        connection = (
            self._env["connections"].get(
                self._config.connection_id,
                None,
            )
            if self._config.connection_id
            else None
        )

        if connection is None:
            raise Exception("Connection not found")

        if task_type == TaskType.CREATE_SESSION:
            # If we have a session and it's not expired, reuse it. Heygen
            # sessions expire after 3 minutes of inactivity.
            if (
                self._config.reuse_session
                and self._heygen_session
                and (time.time() * 1000 - self._heygen_session["created_at"] < 1000 * 60 * 3)
            ):
                result = RealtimeAvatarOutput(
                    task_type=task_type,
                    task_response_json={"data": self._heygen_session["data"]},
                )

                async_to_sync(output_stream.write)(result)
                return output_stream.finalize()
            else:
                url = "https://api.heygen.com/v1/realtime.new"
                body = {
                    "quality": self._config.quality.value,
                    "avatar_name": self._config.avatar_name,
                    "voice": {
                        "voice_id": self._config.voice_id,
                    },
                }

        elif task_type == TaskType.START_SESSION:
            url = "https://api.heygen.com/v1/realtime.start"
            body = {
                **self._input.task_input_json,
                **{"session_id": session_id},
            }

        elif task_type == TaskType.SUBMIT_ICE_CANDIDATE:
            url = "https://api.heygen.com/v1/realtime.ice"
            body = {
                **self._input.task_input_json,
                **{"session_id": session_id},
            }

        elif task_type == TaskType.CLOSE_SESSION:
            url = "https://api.heygen.com/v1/realtime.stop"
            body = body = {"session_id": session_id}

        elif task_type == TaskType.REPEAT or task_type == TaskType.TALK:
            self._disable_history = False
            url = "https://api.heygen.com/v1/realtime.task"
            body = {
                "session_id": session_id,
                "text": (
                    self._messages_to_repeat[self._messages_repeated].strip()
                    if self._config.input_stream
                    else self._input.text
                ),
            }

        response = post(url, json=body, _connection=connection)

        if response.status_code != 200:
            logger.error(f"Error creating task: {response.text}")
            raise Exception("Error creating task")

        if task_type == TaskType.CREATE_SESSION:
            self._heygen_session = {
                "data": response.json()["data"],
                "created_at": time.time() * 1000,
            }

        result = RealtimeAvatarOutput(
            task_type=task_type,
            task_response_json=response.json(),
        )
        async_to_sync(output_stream.write)(result)

        return output_stream.finalize()
