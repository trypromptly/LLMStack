from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

CLICK: BrowserCommandType
COPY: BrowserCommandType
DESCRIPTOR: _descriptor.FileDescriptor
GOTO: BrowserCommandType
RUNNING: RemoteBrowserState
TERMINATE: BrowserCommandType
TERMINATED: RemoteBrowserState
TIMEOUT: RemoteBrowserState
TYPE: BrowserCommandType
WAIT: BrowserCommandType

class BrowserInitData(_message.Message):
    __slots__ = ["persist_session", "session_data", "terminate_url_pattern", "timeout", "url"]
    PERSIST_SESSION_FIELD_NUMBER: _ClassVar[int]
    SESSION_DATA_FIELD_NUMBER: _ClassVar[int]
    TERMINATE_URL_PATTERN_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    persist_session: bool
    session_data: str
    terminate_url_pattern: str
    timeout: int
    url: str
    def __init__(self, url: _Optional[str] = ..., terminate_url_pattern: _Optional[str] = ..., timeout: _Optional[int] = ..., persist_session: bool = ..., session_data: _Optional[str] = ...) -> None: ...

class BrowserInput(_message.Message):
    __slots__ = ["data", "selector", "type"]
    DATA_FIELD_NUMBER: _ClassVar[int]
    SELECTOR_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    data: str
    selector: str
    type: BrowserCommandType
    def __init__(self, type: _Optional[_Union[BrowserCommandType, str]] = ..., selector: _Optional[str] = ..., data: _Optional[str] = ...) -> None: ...

class BrowserOutput(_message.Message):
    __slots__ = ["text", "url"]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    text: str
    url: str
    def __init__(self, url: _Optional[str] = ..., text: _Optional[str] = ...) -> None: ...

class PlaywrightBrowserRequest(_message.Message):
    __slots__ = ["session_data", "steps", "stream_video", "timeout", "url"]
    SESSION_DATA_FIELD_NUMBER: _ClassVar[int]
    STEPS_FIELD_NUMBER: _ClassVar[int]
    STREAM_VIDEO_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    session_data: str
    steps: _containers.RepeatedCompositeFieldContainer[BrowserInput]
    stream_video: bool
    timeout: int
    url: str
    def __init__(self, url: _Optional[str] = ..., steps: _Optional[_Iterable[_Union[BrowserInput, _Mapping]]] = ..., timeout: _Optional[int] = ..., session_data: _Optional[str] = ..., stream_video: bool = ...) -> None: ...

class PlaywrightBrowserResponse(_message.Message):
    __slots__ = ["outputs", "session", "state", "video"]
    OUTPUTS_FIELD_NUMBER: _ClassVar[int]
    SESSION_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    VIDEO_FIELD_NUMBER: _ClassVar[int]
    outputs: _containers.RepeatedCompositeFieldContainer[BrowserOutput]
    session: RemoteBrowserSession
    state: RemoteBrowserState
    video: bytes
    def __init__(self, session: _Optional[_Union[RemoteBrowserSession, _Mapping]] = ..., video: _Optional[bytes] = ..., state: _Optional[_Union[RemoteBrowserState, str]] = ..., outputs: _Optional[_Iterable[_Union[BrowserOutput, _Mapping]]] = ...) -> None: ...

class RemoteBrowserRequest(_message.Message):
    __slots__ = ["init_data", "input"]
    INIT_DATA_FIELD_NUMBER: _ClassVar[int]
    INPUT_FIELD_NUMBER: _ClassVar[int]
    init_data: BrowserInitData
    input: BrowserInput
    def __init__(self, init_data: _Optional[_Union[BrowserInitData, _Mapping]] = ..., input: _Optional[_Union[BrowserInput, _Mapping]] = ...) -> None: ...

class RemoteBrowserResponse(_message.Message):
    __slots__ = ["session", "state"]
    SESSION_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    session: RemoteBrowserSession
    state: RemoteBrowserState
    def __init__(self, session: _Optional[_Union[RemoteBrowserSession, _Mapping]] = ..., state: _Optional[_Union[RemoteBrowserState, str]] = ...) -> None: ...

class RemoteBrowserSession(_message.Message):
    __slots__ = ["session_data", "ws_url"]
    SESSION_DATA_FIELD_NUMBER: _ClassVar[int]
    WS_URL_FIELD_NUMBER: _ClassVar[int]
    session_data: str
    ws_url: str
    def __init__(self, ws_url: _Optional[str] = ..., session_data: _Optional[str] = ...) -> None: ...

class BrowserCommandType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class RemoteBrowserState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
