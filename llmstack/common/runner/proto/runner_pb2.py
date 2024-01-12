# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: runner.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x0crunner.proto"Q\n\x0c\x42rowserInput\x12!\n\x04type\x18\x01 \x01(\x0e\x32\x13.BrowserCommandType\x12\x10\n\x08selector\x18\x02 \x01(\t\x12\x0c\n\x04\x64\x61ta\x18\x03 \x01(\t"}\n\x0f\x42rowserInitData\x12\x0b\n\x03url\x18\x01 \x01(\t\x12\x1d\n\x15terminate_url_pattern\x18\x02 \x01(\t\x12\x0f\n\x07timeout\x18\x03 \x01(\x05\x12\x17\n\x0fpersist_session\x18\x04 \x01(\x08\x12\x14\n\x0csession_data\x18\x05 \x01(\t"*\n\rBrowserOutput\x12\x0b\n\x03url\x18\x01 \x01(\t\x12\x0c\n\x04text\x18\x02 \x01(\t"/\n\rBrowserButton\x12\x10\n\x08selector\x18\x01 \x01(\t\x12\x0c\n\x04text\x18\x02 \x01(\t"3\n\x11\x42rowserInputField\x12\x10\n\x08selector\x18\x01 \x01(\t\x12\x0c\n\x04text\x18\x02 \x01(\t"4\n\x12\x42rowserSelectField\x12\x10\n\x08selector\x18\x01 \x01(\t\x12\x0c\n\x04text\x18\x02 \x01(\t"6\n\x14\x42rowserTextAreaField\x12\x10\n\x08selector\x18\x01 \x01(\t\x12\x0c\n\x04text\x18\x02 \x01(\t":\n\x0b\x42rowserLink\x12\x10\n\x08selector\x18\x01 \x01(\t\x12\x0c\n\x04text\x18\x02 \x01(\t\x12\x0b\n\x03url\x18\x03 \x01(\t"\x9d\x02\n\x0e\x42rowserContent\x12\x0b\n\x03url\x18\x01 \x01(\t\x12\r\n\x05title\x18\x02 \x01(\t\x12\x0c\n\x04html\x18\x03 \x01(\t\x12\x0c\n\x04text\x18\x04 \x01(\t\x12\x12\n\nscreenshot\x18\x05 \x01(\x0c\x12\x1f\n\x07\x62uttons\x18\x06 \x03(\x0b\x32\x0e.BrowserButton\x12"\n\x06inputs\x18\x07 \x03(\x0b\x32\x12.BrowserInputField\x12$\n\x07selects\x18\x08 \x03(\x0b\x32\x13.BrowserSelectField\x12(\n\ttextareas\x18\t \x03(\x0b\x32\x15.BrowserTextAreaField\x12\x1b\n\x05links\x18\n \x03(\x0b\x32\x0c.BrowserLink\x12\r\n\x05\x65rror\x18\x0b \x01(\t"Y\n\x14RemoteBrowserRequest\x12#\n\tinit_data\x18\x01 \x01(\x0b\x32\x10.BrowserInitData\x12\x1c\n\x05input\x18\x05 \x01(\x0b\x32\r.BrowserInput"<\n\x14RemoteBrowserSession\x12\x0e\n\x06ws_url\x18\x01 \x01(\t\x12\x14\n\x0csession_data\x18\x02 \x01(\t"c\n\x15RemoteBrowserResponse\x12&\n\x07session\x18\x01 \x01(\x0b\x32\x15.RemoteBrowserSession\x12"\n\x05state\x18\x02 \x01(\x0e\x32\x13.RemoteBrowserState"\x82\x01\n\x18PlaywrightBrowserRequest\x12\x0b\n\x03url\x18\x01 \x01(\t\x12\x1c\n\x05steps\x18\x02 \x03(\x0b\x32\r.BrowserInput\x12\x0f\n\x07timeout\x18\x03 \x01(\x05\x12\x14\n\x0csession_data\x18\x04 \x01(\t\x12\x14\n\x0cstream_video\x18\x05 \x01(\x08"\xb9\x01\n\x19PlaywrightBrowserResponse\x12&\n\x07session\x18\x01 \x01(\x0b\x32\x15.RemoteBrowserSession\x12\r\n\x05video\x18\x02 \x01(\x0c\x12"\n\x05state\x18\x03 \x01(\x0e\x32\x13.RemoteBrowserState\x12\x1f\n\x07outputs\x18\x04 \x03(\x0b\x32\x0e.BrowserOutput\x12 \n\x07\x63ontent\x18\x05 \x01(\x0b\x32\x0f.BrowserContent*}\n\x12\x42rowserCommandType\x12\x08\n\x04GOTO\x10\x00\x12\r\n\tTERMINATE\x10\x01\x12\x08\n\x04WAIT\x10\x02\x12\t\n\x05\x43LICK\x10\x03\x12\x08\n\x04\x43OPY\x10\x04\x12\x08\n\x04TYPE\x10\x05\x12\x0c\n\x08SCROLL_X\x10\x06\x12\x0c\n\x08SCROLL_Y\x10\x07\x12\t\n\x05\x45NTER\x10\x08*>\n\x12RemoteBrowserState\x12\x0b\n\x07RUNNING\x10\x00\x12\x0e\n\nTERMINATED\x10\x01\x12\x0b\n\x07TIMEOUT\x10\x02\x32\xa6\x01\n\x06Runner\x12G\n\x10GetRemoteBrowser\x12\x15.RemoteBrowserRequest\x1a\x16.RemoteBrowserResponse"\x00(\x01\x30\x01\x12S\n\x14GetPlaywrightBrowser\x12\x19.PlaywrightBrowserRequest\x1a\x1a.PlaywrightBrowserResponse"\x00(\x01\x30\x01\x62\x06proto3'
)

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, "runner_pb2", globals())
if _descriptor._USE_C_DESCRIPTORS == False:
    DESCRIPTOR._options = None
    _BROWSERCOMMANDTYPE._serialized_start = 1635
    _BROWSERCOMMANDTYPE._serialized_end = 1760
    _REMOTEBROWSERSTATE._serialized_start = 1762
    _REMOTEBROWSERSTATE._serialized_end = 1824
    _BROWSERINPUT._serialized_start = 16
    _BROWSERINPUT._serialized_end = 97
    _BROWSERINITDATA._serialized_start = 99
    _BROWSERINITDATA._serialized_end = 224
    _BROWSEROUTPUT._serialized_start = 226
    _BROWSEROUTPUT._serialized_end = 268
    _BROWSERBUTTON._serialized_start = 270
    _BROWSERBUTTON._serialized_end = 317
    _BROWSERINPUTFIELD._serialized_start = 319
    _BROWSERINPUTFIELD._serialized_end = 370
    _BROWSERSELECTFIELD._serialized_start = 372
    _BROWSERSELECTFIELD._serialized_end = 424
    _BROWSERTEXTAREAFIELD._serialized_start = 426
    _BROWSERTEXTAREAFIELD._serialized_end = 480
    _BROWSERLINK._serialized_start = 482
    _BROWSERLINK._serialized_end = 540
    _BROWSERCONTENT._serialized_start = 543
    _BROWSERCONTENT._serialized_end = 828
    _REMOTEBROWSERREQUEST._serialized_start = 830
    _REMOTEBROWSERREQUEST._serialized_end = 919
    _REMOTEBROWSERSESSION._serialized_start = 921
    _REMOTEBROWSERSESSION._serialized_end = 981
    _REMOTEBROWSERRESPONSE._serialized_start = 983
    _REMOTEBROWSERRESPONSE._serialized_end = 1082
    _PLAYWRIGHTBROWSERREQUEST._serialized_start = 1085
    _PLAYWRIGHTBROWSERREQUEST._serialized_end = 1215
    _PLAYWRIGHTBROWSERRESPONSE._serialized_start = 1218
    _PLAYWRIGHTBROWSERRESPONSE._serialized_end = 1403
    _PYTHONCODERUNNERREQUEST._serialized_start = 1405
    _PYTHONCODERUNNERREQUEST._serialized_end = 1461
    _PYTHONCODERUNNERFILE._serialized_start = 1463
    _PYTHONCODERUNNERFILE._serialized_end = 1516
    _PYTHONCODERUNNERRESPONSE._serialized_start = 1518
    _PYTHONCODERUNNERRESPONSE._serialized_end = 1633
    _RUNNER._serialized_start = 1827
    _RUNNER._serialized_end = 2073
# @@protoc_insertion_point(module_scope)
