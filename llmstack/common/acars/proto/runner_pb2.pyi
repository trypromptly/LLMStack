from google.protobuf import struct_pb2 as _struct_pb2
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
HTML: ContentMimeType
JPEG: ContentMimeType
JSON: ContentMimeType
LATEX: ContentMimeType
PDF: ContentMimeType
PNG: ContentMimeType
RUNNING: RemoteBrowserState
SCROLL_X: BrowserCommandType
SCROLL_Y: BrowserCommandType
SVG: ContentMimeType
TERMINATE: BrowserCommandType
TERMINATED: RemoteBrowserState
TEXT: ContentMimeType
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

class CodeRunnerRequest(_message.Message):
    __slots__ = ["files", "session_id", "source_code", "timeout_secs"]
    FILES_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_CODE_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_SECS_FIELD_NUMBER: _ClassVar[int]
    files: _containers.RepeatedCompositeFieldContainer[Content]
    session_id: str
    source_code: str
    timeout_secs: int
    def __init__(self, source_code: _Optional[str] = ..., timeout_secs: _Optional[int] = ..., session_id: _Optional[str] = ..., files: _Optional[_Iterable[_Union[Content, _Mapping]]] = ...) -> None: ...

class CodeRunnerResponse(_message.Message):
    __slots__ = ["files", "state", "stderr", "stdout"]
    FILES_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    STDERR_FIELD_NUMBER: _ClassVar[int]
    STDOUT_FIELD_NUMBER: _ClassVar[int]
    files: _containers.RepeatedCompositeFieldContainer[Content]
    state: RemoteBrowserState
    stderr: str
    stdout: _containers.RepeatedCompositeFieldContainer[Content]
    def __init__(self, state: _Optional[_Union[RemoteBrowserState, str]] = ..., stdout: _Optional[_Iterable[_Union[Content, _Mapping]]] = ..., stderr: _Optional[str] = ..., files: _Optional[_Iterable[_Union[Content, _Mapping]]] = ...) -> None: ...

class Content(_message.Message):
    __slots__ = ["data", "mime_type"]
    DATA_FIELD_NUMBER: _ClassVar[int]
    MIME_TYPE_FIELD_NUMBER: _ClassVar[int]
    data: bytes
    mime_type: ContentMimeType
    def __init__(self, mime_type: _Optional[_Union[ContentMimeType, str]] = ..., data: _Optional[bytes] = ...) -> None: ...

class FileConverterRequest(_message.Message):
    __slots__ = ["file", "options", "target_mime_type"]
    class OptionsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    FILE_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    TARGET_MIME_TYPE_FIELD_NUMBER: _ClassVar[int]
    file: Content
    options: _containers.ScalarMap[str, str]
    target_mime_type: ContentMimeType
    def __init__(self, file: _Optional[_Union[Content, _Mapping]] = ..., target_mime_type: _Optional[_Union[ContentMimeType, str]] = ..., options: _Optional[_Mapping[str, str]] = ...) -> None: ...

class FileConverterResponse(_message.Message):
    __slots__ = ["file"]
    FILE_FIELD_NUMBER: _ClassVar[int]
    file: Content
    def __init__(self, file: _Optional[_Union[Content, _Mapping]] = ...) -> None: ...

class PlaywrightBrowserRequest(_message.Message):
    __slots__ = ["session_data", "skip_tags", "steps", "stream_video", "timeout", "url"]
    SESSION_DATA_FIELD_NUMBER: _ClassVar[int]
    SKIP_TAGS_FIELD_NUMBER: _ClassVar[int]
    STEPS_FIELD_NUMBER: _ClassVar[int]
    STREAM_VIDEO_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    session_data: str
    skip_tags: bool
    steps: _containers.RepeatedCompositeFieldContainer[BrowserInput]
    stream_video: bool
    timeout: int
    url: str
    def __init__(self, url: _Optional[str] = ..., steps: _Optional[_Iterable[_Union[BrowserInput, _Mapping]]] = ..., timeout: _Optional[int] = ..., session_data: _Optional[str] = ..., stream_video: bool = ..., skip_tags: bool = ...) -> None: ...

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

class RestrictedPythonCodeRunnerRequest(_message.Message):
    __slots__ = ["input_data", "source_code", "timeout_secs"]
    INPUT_DATA_FIELD_NUMBER: _ClassVar[int]
    SOURCE_CODE_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_SECS_FIELD_NUMBER: _ClassVar[int]
    input_data: _struct_pb2.Struct
    source_code: str
    timeout_secs: int
    def __init__(self, source_code: _Optional[str] = ..., input_data: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., timeout_secs: _Optional[int] = ...) -> None: ...

class RestrictedPythonCodeRunnerResponse(_message.Message):
    __slots__ = ["exit_code", "local_variables", "state", "stderr", "stdout"]
    EXIT_CODE_FIELD_NUMBER: _ClassVar[int]
    LOCAL_VARIABLES_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    STDERR_FIELD_NUMBER: _ClassVar[int]
    STDOUT_FIELD_NUMBER: _ClassVar[int]
    exit_code: int
    local_variables: _struct_pb2.Struct
    state: RemoteBrowserState
    stderr: str
    stdout: _containers.RepeatedCompositeFieldContainer[Content]
    def __init__(self, state: _Optional[_Union[RemoteBrowserState, str]] = ..., local_variables: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., stdout: _Optional[_Iterable[_Union[Content, _Mapping]]] = ..., stderr: _Optional[str] = ..., exit_code: _Optional[int] = ...) -> None: ...

class ContentMimeType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class BrowserCommandType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class RemoteBrowserState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
