from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor
GOTO: BrowserCommandType
RUNNING: RemoteBrowserState
TERMINATE: BrowserCommandType
TERMINATED: RemoteBrowserState
TIMEOUT: RemoteBrowserState

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
    __slots__ = ["data", "type"]
    DATA_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    data: str
    type: BrowserCommandType
    def __init__(self, type: _Optional[_Union[BrowserCommandType, str]] = ..., data: _Optional[str] = ...) -> None: ...

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
