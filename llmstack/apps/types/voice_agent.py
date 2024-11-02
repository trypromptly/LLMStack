from typing import Any, Dict, Literal, Optional, Union

from pydantic import Field

from llmstack.apps.types.app_type_interface import AppTypeInterface, BaseSchema
from llmstack.common.blocks.base.schema import StrEnum


class MultiModalModelProvider(StrEnum):
    OPENAI = "openai"


class TextToSpeechSettings(BaseSchema):
    provider: str = Field(
        default="elevenlabs",
        title="Provider",
        description="The provider to use for the text to speech.",
    )
    model: str = Field(
        default="eleven_multilingual_v2",
        title="Model",
        description="The model to use for the text to speech.",
    )
    config: Dict[str, Any] = Field(
        default={},
        title="Config",
        description="The config to use for the text to speech.",
    )


class SpeechToTextSettings(BaseSchema):
    provider: str = Field(
        default="elevenlabs",
        title="Provider",
        description="The provider to use for the speech to text.",
    )
    model: str = Field(
        default="eleven_multilingual_v2",
        title="Model",
        description="The model to use for the speech to text.",
    )
    config: Dict[str, Any] = Field(
        default={},
        title="Config",
        description="The config to use for the speech to text.",
    )


class VoiceActivityDetectionSettings(BaseSchema):
    threshold: float = Field(
        default=0.5,
        title="Threshold",
        description="The threshold to use for the voice activity detection.",
    )
    prefix_padding_ms: int = Field(
        default=300,
        title="Prefix Padding",
        description="The amount of padding to add to the start of the audio to ensure we get the full utterance.",
    )
    silence_duration_ms: int = Field(
        default=500,
        title="Silence Duration",
        description="The duration of silence to use to detect the end of an utterance.",
    )


class MultiModal(BaseSchema):
    backend_type: Literal["multi_modal"] = Field(
        default="multi_modal",
        title="Backend Type",
        description="The backend type to use for the multi modal model.",
        json_schema_extra={"widget": "hidden", "readOnly": True},
    )
    provider: MultiModalModelProvider = Field(
        default=MultiModalModelProvider.OPENAI,
        title="Model Provider",
        description="The provider to use for the multi modal model.",
        json_schema_extra={"widget": "customselect"},
    )
    model: str = Field(
        default="gpt-4o-realtime",
        title="Model Slug",
        description="The slug of the multi modal model to use.",
        json_schema_extra={"widget": "customselect"},
    )
    temperature: Optional[float] = Field(
        title="Temperature",
        default=0.7,
        description="Temperature to use for the agent",
        json_schema_extra={"advanced_parameter": True},
        ge=0.0,
        le=1.0,
    )
    turn_detection_threshold: float = Field(
        default=0.5,
        title="Turn Detection Threshold",
        description="The threshold to use for the turn detection.",
        json_schema_extra={"advanced_parameter": True},
    )
    turn_detection_prefix_padding_ms: int = Field(
        default=300,
        title="Turn Detection Prefix Padding",
        description="The amount of padding to add to the start of the audio to ensure we get the full utterance.",
        json_schema_extra={"advanced_parameter": True},
    )
    turn_detection_silence_duration_ms: int = Field(
        default=500,
        title="Turn Detection Silence Duration",
        description="The duration of silence to use to detect the end of an utterance.",
        json_schema_extra={"advanced_parameter": True},
    )


class CustomPipeline(BaseSchema):
    backend_type: Literal["custom_pipeline"] = Field(
        default="custom_pipeline",
        title="Backend Type",
        description="The backend type to use for the custom pipeline.",
        json_schema_extra={"widget": "hidden", "readOnly": True},
    )
    speech_to_text_model_provider: str = Field(
        default="openai",
        title="Speech To Text Model Provider",
        description="The provider to use for the speech to text model.",
        json_schema_extra={"widget": "customselect", "options": ["openai"]},
    )
    speech_to_text_model_slug: str = Field(
        default="whisper-1",
        title="Speech To Text Model Slug",
        description="The slug of the speech to text model to use.",
        json_schema_extra={"widget": "customselect", "options": []},
    )
    provider: str = Field(
        default="openai",
        title="Model Provider",
        description="The provider to use for the model.",
        json_schema_extra={"widget": "customselect", "options": ["openai"]},
    )
    model: str = Field(
        default="gpt-4o-realtime",
        title="Model Slug",
        description="The slug of the model to use.",
        json_schema_extra={"widget": "customselect", "options": []},
    )
    stream: Optional[bool] = Field(
        default=None,
        title="Stream",
        description="Stream the output from the agent model",
        json_schema_extra={"advanced_parameter": True},
    )
    turn_detection_prefix_padding_ms: int = Field(
        default=300,
        title="Turn Detection Prefix Padding",
        description="The amount of padding to add to the start of the audio to ensure we get the full utterance.",
        json_schema_extra={"advanced_parameter": True},
    )
    turn_detection_silence_duration_ms: int = Field(
        default=500,
        title="Turn Detection Silence Duration",
        description="The duration of silence to use to detect the end of an utterance.",
        json_schema_extra={"advanced_parameter": True},
    )
    text_to_speech_model_provider: str = Field(
        default="elevenlabs",
        title="Text To Speech Model Provider",
        description="The provider to use for the text to speech model.",
        json_schema_extra={"widget": "customselect", "options": ["elevenlabs"]},
    )
    text_to_speech_model_slug: str = Field(
        default="eleven_multilingual_v2",
        title="Text To Speech Model Slug",
        description="The slug of the text to speech model to use.",
        json_schema_extra={"widget": "customselect", "options": []},
    )


class VoiceAgentConfigSchema(BaseSchema):
    system_message: str = Field(
        title="System Message",
        default="You are a helpful assistant that uses provided tools to perform actions.",
        description="The system message to use with the Agent.",
        json_schema_extra={"widget": "textarea"},
    )
    max_steps: int = Field(
        title="Max Steps",
        default=10,
        description="The maximum number of steps the agent can take.",
        json_schema_extra={"advanced_parameter": True},
        le=100,
        ge=1,
    )
    backend: Union[MultiModal, CustomPipeline] = Field(
        default=MultiModal(),
        title="Backend",
        description="The backend to use for the voice agent.",
    )
    input_audio_format: Optional[str] = Field(
        default=None,
        title="Input Audio Format",
        description="The audio format to use for the input.",
        json_schema_extra={"widget": "hidden"},
    )
    output_audio_format: Optional[str] = Field(
        default=None,
        title="Output Audio Format",
        description="The audio format to use for the output.",
        json_schema_extra={"widget": "hidden"},
    )


class VoiceAgent(AppTypeInterface[VoiceAgentConfigSchema]):
    @staticmethod
    def slug() -> str:
        return "voice-agent"

    @staticmethod
    def name() -> str:
        return "Voice Agent"

    @staticmethod
    def description() -> str:
        return "Voice based conversational agents that can perform actions based on user input"
