from typing import ClassVar as _ClassVar
from typing import Iterable as _Iterable
from typing import Mapping as _Mapping
from typing import Optional as _Optional
from typing import Union as _Union

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper

DESCRIPTOR: _descriptor.FileDescriptor

class ContentMimeType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TEXT: _ClassVar[ContentMimeType]
    JSON: _ClassVar[ContentMimeType]
    HTML: _ClassVar[ContentMimeType]
    PNG: _ClassVar[ContentMimeType]
    JPEG: _ClassVar[ContentMimeType]
    SVG: _ClassVar[ContentMimeType]
    PDF: _ClassVar[ContentMimeType]
    LATEX: _ClassVar[ContentMimeType]

class BrowserCommandType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    GOTO: _ClassVar[BrowserCommandType]
    TERMINATE: _ClassVar[BrowserCommandType]
    WAIT: _ClassVar[BrowserCommandType]
    CLICK: _ClassVar[BrowserCommandType]
    COPY: _ClassVar[BrowserCommandType]
    TYPE: _ClassVar[BrowserCommandType]
    SCROLL_X: _ClassVar[BrowserCommandType]
    SCROLL_Y: _ClassVar[BrowserCommandType]
    ENTER: _ClassVar[BrowserCommandType]

class RemoteBrowserState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RUNNING: _ClassVar[RemoteBrowserState]
    TERMINATED: _ClassVar[RemoteBrowserState]
    TIMEOUT: _ClassVar[RemoteBrowserState]

TEXT: ContentMimeType
JSON: ContentMimeType
HTML: ContentMimeType
PNG: ContentMimeType
JPEG: ContentMimeType
SVG: ContentMimeType
PDF: ContentMimeType
LATEX: ContentMimeType
GOTO: BrowserCommandType
TERMINATE: BrowserCommandType
WAIT: BrowserCommandType
CLICK: BrowserCommandType
COPY: BrowserCommandType
TYPE: BrowserCommandType
SCROLL_X: BrowserCommandType
SCROLL_Y: BrowserCommandType
ENTER: BrowserCommandType
RUNNING: RemoteBrowserState
TERMINATED: RemoteBrowserState
TIMEOUT: RemoteBrowserState

class Content(_message.Message):
    __slots__ = ("mime_type", "data")
    MIME_TYPE_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    mime_type: ContentMimeType
    data: bytes
    def __init__(
        self, mime_type: _Optional[_Union[ContentMimeType, str]] = ..., data: _Optional[bytes] = ...
    ) -> None: ...

class BrowserInput(_message.Message):
    __slots__ = ("type", "selector", "data")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    SELECTOR_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    type: BrowserCommandType
    selector: str
    data: str
    def __init__(
        self,
        type: _Optional[_Union[BrowserCommandType, str]] = ...,
        selector: _Optional[str] = ...,
        data: _Optional[str] = ...,
    ) -> None: ...

class BrowserInitData(_message.Message):
    __slots__ = ("url", "terminate_url_pattern", "timeout", "persist_session", "session_data")
    URL_FIELD_NUMBER: _ClassVar[int]
    TERMINATE_URL_PATTERN_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    PERSIST_SESSION_FIELD_NUMBER: _ClassVar[int]
    SESSION_DATA_FIELD_NUMBER: _ClassVar[int]
    url: str
    terminate_url_pattern: str
    timeout: int
    persist_session: bool
    session_data: str
    def __init__(
        self,
        url: _Optional[str] = ...,
        terminate_url_pattern: _Optional[str] = ...,
        timeout: _Optional[int] = ...,
        persist_session: bool = ...,
        session_data: _Optional[str] = ...,
    ) -> None: ...

class BrowserOutput(_message.Message):
    __slots__ = ("url", "text")
    URL_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    url: str
    text: str
    def __init__(self, url: _Optional[str] = ..., text: _Optional[str] = ...) -> None: ...

class BrowserButton(_message.Message):
    __slots__ = ("selector", "text")
    SELECTOR_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    selector: str
    text: str
    def __init__(self, selector: _Optional[str] = ..., text: _Optional[str] = ...) -> None: ...

class BrowserInputField(_message.Message):
    __slots__ = ("selector", "text")
    SELECTOR_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    selector: str
    text: str
    def __init__(self, selector: _Optional[str] = ..., text: _Optional[str] = ...) -> None: ...

class BrowserSelectField(_message.Message):
    __slots__ = ("selector", "text")
    SELECTOR_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    selector: str
    text: str
    def __init__(self, selector: _Optional[str] = ..., text: _Optional[str] = ...) -> None: ...

class BrowserTextAreaField(_message.Message):
    __slots__ = ("selector", "text")
    SELECTOR_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    selector: str
    text: str
    def __init__(self, selector: _Optional[str] = ..., text: _Optional[str] = ...) -> None: ...

class BrowserLink(_message.Message):
    __slots__ = ("selector", "text", "url")
    SELECTOR_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    selector: str
    text: str
    url: str
    def __init__(
        self, selector: _Optional[str] = ..., text: _Optional[str] = ..., url: _Optional[str] = ...
    ) -> None: ...

class BrowserContent(_message.Message):
    __slots__ = (
        "url",
        "title",
        "html",
        "text",
        "screenshot",
        "buttons",
        "inputs",
        "selects",
        "textareas",
        "links",
        "error",
    )
    URL_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    HTML_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    SCREENSHOT_FIELD_NUMBER: _ClassVar[int]
    BUTTONS_FIELD_NUMBER: _ClassVar[int]
    INPUTS_FIELD_NUMBER: _ClassVar[int]
    SELECTS_FIELD_NUMBER: _ClassVar[int]
    TEXTAREAS_FIELD_NUMBER: _ClassVar[int]
    LINKS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    url: str
    title: str
    html: str
    text: str
    screenshot: bytes
    buttons: _containers.RepeatedCompositeFieldContainer[BrowserButton]
    inputs: _containers.RepeatedCompositeFieldContainer[BrowserInputField]
    selects: _containers.RepeatedCompositeFieldContainer[BrowserSelectField]
    textareas: _containers.RepeatedCompositeFieldContainer[BrowserTextAreaField]
    links: _containers.RepeatedCompositeFieldContainer[BrowserLink]
    error: str
    def __init__(
        self,
        url: _Optional[str] = ...,
        title: _Optional[str] = ...,
        html: _Optional[str] = ...,
        text: _Optional[str] = ...,
        screenshot: _Optional[bytes] = ...,
        buttons: _Optional[_Iterable[_Union[BrowserButton, _Mapping]]] = ...,
        inputs: _Optional[_Iterable[_Union[BrowserInputField, _Mapping]]] = ...,
        selects: _Optional[_Iterable[_Union[BrowserSelectField, _Mapping]]] = ...,
        textareas: _Optional[_Iterable[_Union[BrowserTextAreaField, _Mapping]]] = ...,
        links: _Optional[_Iterable[_Union[BrowserLink, _Mapping]]] = ...,
        error: _Optional[str] = ...,
    ) -> None: ...

class RemoteBrowserRequest(_message.Message):
    __slots__ = ("init_data", "input")
    INIT_DATA_FIELD_NUMBER: _ClassVar[int]
    INPUT_FIELD_NUMBER: _ClassVar[int]
    init_data: BrowserInitData
    input: BrowserInput
    def __init__(
        self,
        init_data: _Optional[_Union[BrowserInitData, _Mapping]] = ...,
        input: _Optional[_Union[BrowserInput, _Mapping]] = ...,
    ) -> None: ...

class RemoteBrowserSession(_message.Message):
    __slots__ = ("ws_url", "session_data")
    WS_URL_FIELD_NUMBER: _ClassVar[int]
    SESSION_DATA_FIELD_NUMBER: _ClassVar[int]
    ws_url: str
    session_data: str
    def __init__(self, ws_url: _Optional[str] = ..., session_data: _Optional[str] = ...) -> None: ...

class RemoteBrowserResponse(_message.Message):
    __slots__ = ("session", "state")
    SESSION_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    session: RemoteBrowserSession
    state: RemoteBrowserState
    def __init__(
        self,
        session: _Optional[_Union[RemoteBrowserSession, _Mapping]] = ...,
        state: _Optional[_Union[RemoteBrowserState, str]] = ...,
    ) -> None: ...

class PlaywrightBrowserRequest(_message.Message):
    __slots__ = ("url", "steps", "timeout", "session_data", "stream_video")
    URL_FIELD_NUMBER: _ClassVar[int]
    STEPS_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    SESSION_DATA_FIELD_NUMBER: _ClassVar[int]
    STREAM_VIDEO_FIELD_NUMBER: _ClassVar[int]
    url: str
    steps: _containers.RepeatedCompositeFieldContainer[BrowserInput]
    timeout: int
    session_data: str
    stream_video: bool
    def __init__(
        self,
        url: _Optional[str] = ...,
        steps: _Optional[_Iterable[_Union[BrowserInput, _Mapping]]] = ...,
        timeout: _Optional[int] = ...,
        session_data: _Optional[str] = ...,
        stream_video: bool = ...,
    ) -> None: ...

class PlaywrightBrowserResponse(_message.Message):
    __slots__ = ("session", "video", "state", "outputs", "content")
    SESSION_FIELD_NUMBER: _ClassVar[int]
    VIDEO_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    OUTPUTS_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    session: RemoteBrowserSession
    video: bytes
    state: RemoteBrowserState
    outputs: _containers.RepeatedCompositeFieldContainer[BrowserOutput]
    content: BrowserContent
    def __init__(
        self,
        session: _Optional[_Union[RemoteBrowserSession, _Mapping]] = ...,
        video: _Optional[bytes] = ...,
        state: _Optional[_Union[RemoteBrowserState, str]] = ...,
        outputs: _Optional[_Iterable[_Union[BrowserOutput, _Mapping]]] = ...,
        content: _Optional[_Union[BrowserContent, _Mapping]] = ...,
    ) -> None: ...

class PythonCodeRunnerFile(_message.Message):
    __slots__ = ("name", "content")
    NAME_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    name: str
    content: bytes
    def __init__(self, name: _Optional[str] = ..., content: _Optional[bytes] = ...) -> None: ...

class RestrictedPythonCodeRunnerRequest(_message.Message):
    __slots__ = ("source_code", "input_data", "timeout_secs")
    SOURCE_CODE_FIELD_NUMBER: _ClassVar[int]
    INPUT_DATA_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_SECS_FIELD_NUMBER: _ClassVar[int]
    source_code: str
    input_data: _struct_pb2.Struct
    timeout_secs: int
    def __init__(
        self,
        source_code: _Optional[str] = ...,
        input_data: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...,
        timeout_secs: _Optional[int] = ...,
    ) -> None: ...

class RestrictedPythonCodeRunnerResponse(_message.Message):
    __slots__ = ("state", "local_variables", "stdout", "stderr", "exit_code")
    STATE_FIELD_NUMBER: _ClassVar[int]
    LOCAL_VARIABLES_FIELD_NUMBER: _ClassVar[int]
    STDOUT_FIELD_NUMBER: _ClassVar[int]
    STDERR_FIELD_NUMBER: _ClassVar[int]
    EXIT_CODE_FIELD_NUMBER: _ClassVar[int]
    state: RemoteBrowserState
    local_variables: _struct_pb2.Struct
    stdout: _containers.RepeatedCompositeFieldContainer[Content]
    stderr: str
    exit_code: int
    def __init__(
        self,
        state: _Optional[_Union[RemoteBrowserState, str]] = ...,
        local_variables: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...,
        stdout: _Optional[_Iterable[_Union[Content, _Mapping]]] = ...,
        stderr: _Optional[str] = ...,
        exit_code: _Optional[int] = ...,
    ) -> None: ...

class CodeRunnerRequest(_message.Message):
    __slots__ = ("source_code", "timeout_secs", "session_id", "files")
    SOURCE_CODE_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_SECS_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    FILES_FIELD_NUMBER: _ClassVar[int]
    source_code: str
    timeout_secs: int
    session_id: str
    files: _containers.RepeatedCompositeFieldContainer[Content]
    def __init__(
        self,
        source_code: _Optional[str] = ...,
        timeout_secs: _Optional[int] = ...,
        session_id: _Optional[str] = ...,
        files: _Optional[_Iterable[_Union[Content, _Mapping]]] = ...,
    ) -> None: ...

class CodeRunnerResponse(_message.Message):
    __slots__ = ("state", "stdout", "stderr", "files")
    STATE_FIELD_NUMBER: _ClassVar[int]
    STDOUT_FIELD_NUMBER: _ClassVar[int]
    STDERR_FIELD_NUMBER: _ClassVar[int]
    FILES_FIELD_NUMBER: _ClassVar[int]
    state: RemoteBrowserState
    stdout: _containers.RepeatedCompositeFieldContainer[Content]
    stderr: str
    files: _containers.RepeatedCompositeFieldContainer[Content]
    def __init__(
        self,
        state: _Optional[_Union[RemoteBrowserState, str]] = ...,
        stdout: _Optional[_Iterable[_Union[Content, _Mapping]]] = ...,
        stderr: _Optional[str] = ...,
        files: _Optional[_Iterable[_Union[Content, _Mapping]]] = ...,
    ) -> None: ...

class WordProcessorFileCreate(_message.Message):
    __slots__ = ("filename", "mime_type", "html")
    FILENAME_FIELD_NUMBER: _ClassVar[int]
    MIME_TYPE_FIELD_NUMBER: _ClassVar[int]
    HTML_FIELD_NUMBER: _ClassVar[int]
    filename: str
    mime_type: ContentMimeType
    html: str
    def __init__(
        self,
        filename: _Optional[str] = ...,
        mime_type: _Optional[_Union[ContentMimeType, str]] = ...,
        html: _Optional[str] = ...,
    ) -> None: ...

class WordProcessorFileRead(_message.Message):
    __slots__ = ("file", "read_as_text", "read_as_html", "read_as_unstructured")
    FILE_FIELD_NUMBER: _ClassVar[int]
    READ_AS_TEXT_FIELD_NUMBER: _ClassVar[int]
    READ_AS_HTML_FIELD_NUMBER: _ClassVar[int]
    READ_AS_UNSTRUCTURED_FIELD_NUMBER: _ClassVar[int]
    file: Content
    read_as_text: bool
    read_as_html: bool
    read_as_unstructured: bool
    def __init__(
        self,
        file: _Optional[_Union[Content, _Mapping]] = ...,
        read_as_text: bool = ...,
        read_as_html: bool = ...,
        read_as_unstructured: bool = ...,
    ) -> None: ...

class WordProcessorRequest(_message.Message):
    __slots__ = ("create", "read")
    CREATE_FIELD_NUMBER: _ClassVar[int]
    READ_FIELD_NUMBER: _ClassVar[int]
    create: WordProcessorFileCreate
    read: WordProcessorFileRead
    def __init__(
        self,
        create: _Optional[_Union[WordProcessorFileCreate, _Mapping]] = ...,
        read: _Optional[_Union[WordProcessorFileRead, _Mapping]] = ...,
    ) -> None: ...

class FileConverterRequest(_message.Message):
    __slots__ = ("file", "target_mime_type", "options")

    class OptionsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

    FILE_FIELD_NUMBER: _ClassVar[int]
    TARGET_MIME_TYPE_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    file: Content
    target_mime_type: ContentMimeType
    options: _containers.ScalarMap[str, str]
    def __init__(
        self,
        file: _Optional[_Union[Content, _Mapping]] = ...,
        target_mime_type: _Optional[_Union[ContentMimeType, str]] = ...,
        options: _Optional[_Mapping[str, str]] = ...,
    ) -> None: ...

class FileConverterResponse(_message.Message):
    __slots__ = ("file",)
    FILE_FIELD_NUMBER: _ClassVar[int]
    file: Content
    def __init__(self, file: _Optional[_Union[Content, _Mapping]] = ...) -> None: ...

class WordProcessorResponse(_message.Message):
    __slots__ = ("data", "data_as_text", "data_as_html", "data_as_unstructured", "files")
    DATA_FIELD_NUMBER: _ClassVar[int]
    DATA_AS_TEXT_FIELD_NUMBER: _ClassVar[int]
    DATA_AS_HTML_FIELD_NUMBER: _ClassVar[int]
    DATA_AS_UNSTRUCTURED_FIELD_NUMBER: _ClassVar[int]
    FILES_FIELD_NUMBER: _ClassVar[int]
    data: bytes
    data_as_text: bool
    data_as_html: bool
    data_as_unstructured: bool
    files: _containers.RepeatedCompositeFieldContainer[Content]
    def __init__(
        self,
        data: _Optional[bytes] = ...,
        data_as_text: bool = ...,
        data_as_html: bool = ...,
        data_as_unstructured: bool = ...,
        files: _Optional[_Iterable[_Union[Content, _Mapping]]] = ...,
    ) -> None: ...
