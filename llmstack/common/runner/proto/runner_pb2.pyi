from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

CLICK: BrowserCommandType
COPY: BrowserCommandType
DESCRIPTOR: _descriptor.FileDescriptor
ENTER: BrowserCommandType
GOTO: BrowserCommandType
RUNNING: RemoteBrowserState
SCROLL_X: BrowserCommandType
SCROLL_Y: BrowserCommandType
TERMINATE: BrowserCommandType
TERMINATED: RemoteBrowserState
TIMEOUT: RemoteBrowserState
TYPE: BrowserCommandType
WAIT: BrowserCommandType

class BrowserButton(_message.Message):
    __slots__ = ["selector", "text"]
    SELECTOR_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    selector: str
    text: str
    def __init__(self, selector: _Optional[str] = ..., text: _Optional[str] = ...) -> None: ...

class BrowserContent(_message.Message):
    __slots__ = ["buttons", "error", "html", "inputs", "links", "screenshot", "selects", "text", "textareas", "title", "url"]
    BUTTONS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    HTML_FIELD_NUMBER: _ClassVar[int]
    INPUTS_FIELD_NUMBER: _ClassVar[int]
    LINKS_FIELD_NUMBER: _ClassVar[int]
    SCREENSHOT_FIELD_NUMBER: _ClassVar[int]
    SELECTS_FIELD_NUMBER: _ClassVar[int]
    TEXTAREAS_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    buttons: _containers.RepeatedCompositeFieldContainer[BrowserButton]
    error: str
    html: str
    inputs: _containers.RepeatedCompositeFieldContainer[BrowserInputField]
    links: _containers.RepeatedCompositeFieldContainer[BrowserLink]
    screenshot: bytes
    selects: _containers.RepeatedCompositeFieldContainer[BrowserSelectField]
    text: str
    textareas: _containers.RepeatedCompositeFieldContainer[BrowserTextAreaField]
    title: str
    url: str
    def __init__(self, url: _Optional[str] = ..., title: _Optional[str] = ..., html: _Optional[str] = ..., text: _Optional[str] = ..., screenshot: _Optional[bytes] = ..., buttons: _Optional[_Iterable[_Union[BrowserButton, _Mapping]]] = ..., inputs: _Optional[_Iterable[_Union[BrowserInputField, _Mapping]]] = ..., selects: _Optional[_Iterable[_Union[BrowserSelectField, _Mapping]]] = ..., textareas: _Optional[_Iterable[_Union[BrowserTextAreaField, _Mapping]]] = ..., links: _Optional[_Iterable[_Union[BrowserLink, _Mapping]]] = ..., error: _Optional[str] = ...) -> None: ...

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

class BrowserInputField(_message.Message):
    __slots__ = ["selector", "text"]
    SELECTOR_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    selector: str
    text: str
    def __init__(self, selector: _Optional[str] = ..., text: _Optional[str] = ...) -> None: ...

class BrowserLink(_message.Message):
    __slots__ = ["selector", "text", "url"]
    SELECTOR_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    selector: str
    text: str
    url: str
    def __init__(self, selector: _Optional[str] = ..., text: _Optional[str] = ..., url: _Optional[str] = ...) -> None: ...

class BrowserOutput(_message.Message):
    __slots__ = ["text", "url"]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    text: str
    url: str
    def __init__(self, url: _Optional[str] = ..., text: _Optional[str] = ...) -> None: ...

class BrowserSelectField(_message.Message):
    __slots__ = ["selector", "text"]
    SELECTOR_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    selector: str
    text: str
    def __init__(self, selector: _Optional[str] = ..., text: _Optional[str] = ...) -> None: ...

class BrowserTextAreaField(_message.Message):
    __slots__ = ["selector", "text"]
    SELECTOR_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    selector: str
    text: str
    def __init__(self, selector: _Optional[str] = ..., text: _Optional[str] = ...) -> None: ...

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
    __slots__ = ["content", "outputs", "session", "state", "video"]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    OUTPUTS_FIELD_NUMBER: _ClassVar[int]
    SESSION_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    VIDEO_FIELD_NUMBER: _ClassVar[int]
    content: BrowserContent
    outputs: _containers.RepeatedCompositeFieldContainer[BrowserOutput]
    session: RemoteBrowserSession
    state: RemoteBrowserState
    video: bytes
    def __init__(self, session: _Optional[_Union[RemoteBrowserSession, _Mapping]] = ..., video: _Optional[bytes] = ..., state: _Optional[_Union[RemoteBrowserState, str]] = ..., outputs: _Optional[_Iterable[_Union[BrowserOutput, _Mapping]]] = ..., content: _Optional[_Union[BrowserContent, _Mapping]] = ...) -> None: ...

class PythonCodeRunnerFile(_message.Message):
    __slots__ = ["content", "name"]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    content: bytes
    name: str
    def __init__(self, name: _Optional[str] = ..., content: _Optional[bytes] = ...) -> None: ...

class PythonCodeRunnerRequest(_message.Message):
    __slots__ = ["code", "timeout"]
    CODE_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    code: str
    timeout: int
    def __init__(self, code: _Optional[str] = ..., timeout: _Optional[int] = ...) -> None: ...

class PythonCodeRunnerResponse(_message.Message):
    __slots__ = ["exit_code", "files", "stderr", "stdout"]
    EXIT_CODE_FIELD_NUMBER: _ClassVar[int]
    FILES_FIELD_NUMBER: _ClassVar[int]
    STDERR_FIELD_NUMBER: _ClassVar[int]
    STDOUT_FIELD_NUMBER: _ClassVar[int]
    exit_code: str
    files: _containers.RepeatedCompositeFieldContainer[PythonCodeRunnerFile]
    stderr: _containers.RepeatedScalarFieldContainer[str]
    stdout: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, stdout: _Optional[_Iterable[str]] = ..., stderr: _Optional[_Iterable[str]] = ..., exit_code: _Optional[str] = ..., files: _Optional[_Iterable[_Union[PythonCodeRunnerFile, _Mapping]]] = ...) -> None: ...

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
