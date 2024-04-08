# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: runner.proto
# Protobuf Python Version: 4.25.1
# flake8: noqa
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import struct_pb2 as google_dot_protobuf_dot_struct__pb2

DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x0crunner.proto\x1a\x1cgoogle/protobuf/struct.proto"<\n\x07\x43ontent\x12#\n\tmime_type\x18\x01 \x01(\x0e\x32\x10.ContentMimeType\x12\x0c\n\x04\x64\x61ta\x18\x02 \x01(\x0c"Q\n\x0c\x42rowserInput\x12!\n\x04type\x18\x01 \x01(\x0e\x32\x13.BrowserCommandType\x12\x10\n\x08selector\x18\x02 \x01(\t\x12\x0c\n\x04\x64\x61ta\x18\x03 \x01(\t"}\n\x0f\x42rowserInitData\x12\x0b\n\x03url\x18\x01 \x01(\t\x12\x1d\n\x15terminate_url_pattern\x18\x02 \x01(\t\x12\x0f\n\x07timeout\x18\x03 \x01(\x05\x12\x17\n\x0fpersist_session\x18\x04 \x01(\x08\x12\x14\n\x0csession_data\x18\x05 \x01(\t"*\n\rBrowserOutput\x12\x0b\n\x03url\x18\x01 \x01(\t\x12\x0c\n\x04text\x18\x02 \x01(\t"/\n\rBrowserButton\x12\x10\n\x08selector\x18\x01 \x01(\t\x12\x0c\n\x04text\x18\x02 \x01(\t"3\n\x11\x42rowserInputField\x12\x10\n\x08selector\x18\x01 \x01(\t\x12\x0c\n\x04text\x18\x02 \x01(\t"4\n\x12\x42rowserSelectField\x12\x10\n\x08selector\x18\x01 \x01(\t\x12\x0c\n\x04text\x18\x02 \x01(\t"6\n\x14\x42rowserTextAreaField\x12\x10\n\x08selector\x18\x01 \x01(\t\x12\x0c\n\x04text\x18\x02 \x01(\t":\n\x0b\x42rowserLink\x12\x10\n\x08selector\x18\x01 \x01(\t\x12\x0c\n\x04text\x18\x02 \x01(\t\x12\x0b\n\x03url\x18\x03 \x01(\t"\x9d\x02\n\x0e\x42rowserContent\x12\x0b\n\x03url\x18\x01 \x01(\t\x12\r\n\x05title\x18\x02 \x01(\t\x12\x0c\n\x04html\x18\x03 \x01(\t\x12\x0c\n\x04text\x18\x04 \x01(\t\x12\x12\n\nscreenshot\x18\x05 \x01(\x0c\x12\x1f\n\x07\x62uttons\x18\x06 \x03(\x0b\x32\x0e.BrowserButton\x12"\n\x06inputs\x18\x07 \x03(\x0b\x32\x12.BrowserInputField\x12$\n\x07selects\x18\x08 \x03(\x0b\x32\x13.BrowserSelectField\x12(\n\ttextareas\x18\t \x03(\x0b\x32\x15.BrowserTextAreaField\x12\x1b\n\x05links\x18\n \x03(\x0b\x32\x0c.BrowserLink\x12\r\n\x05\x65rror\x18\x0b \x01(\t"Y\n\x14RemoteBrowserRequest\x12#\n\tinit_data\x18\x01 \x01(\x0b\x32\x10.BrowserInitData\x12\x1c\n\x05input\x18\x05 \x01(\x0b\x32\r.BrowserInput"<\n\x14RemoteBrowserSession\x12\x0e\n\x06ws_url\x18\x01 \x01(\t\x12\x14\n\x0csession_data\x18\x02 \x01(\t"c\n\x15RemoteBrowserResponse\x12&\n\x07session\x18\x01 \x01(\x0b\x32\x15.RemoteBrowserSession\x12"\n\x05state\x18\x02 \x01(\x0e\x32\x13.RemoteBrowserState"\x82\x01\n\x18PlaywrightBrowserRequest\x12\x0b\n\x03url\x18\x01 \x01(\t\x12\x1c\n\x05steps\x18\x02 \x03(\x0b\x32\r.BrowserInput\x12\x0f\n\x07timeout\x18\x03 \x01(\x05\x12\x14\n\x0csession_data\x18\x04 \x01(\t\x12\x14\n\x0cstream_video\x18\x05 \x01(\x08"\xb9\x01\n\x19PlaywrightBrowserResponse\x12&\n\x07session\x18\x01 \x01(\x0b\x32\x15.RemoteBrowserSession\x12\r\n\x05video\x18\x02 \x01(\x0c\x12"\n\x05state\x18\x03 \x01(\x0e\x32\x13.RemoteBrowserState\x12\x1f\n\x07outputs\x18\x04 \x03(\x0b\x32\x0e.BrowserOutput\x12 \n\x07\x63ontent\x18\x05 \x01(\x0b\x32\x0f.BrowserContent"5\n\x14PythonCodeRunnerFile\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0f\n\x07\x63ontent\x18\x02 \x01(\x0c"{\n!RestrictedPythonCodeRunnerRequest\x12\x13\n\x0bsource_code\x18\x01 \x01(\t\x12+\n\ninput_data\x18\x02 \x01(\x0b\x32\x17.google.protobuf.Struct\x12\x14\n\x0ctimeout_secs\x18\x03 \x01(\x05"\xb7\x01\n"RestrictedPythonCodeRunnerResponse\x12"\n\x05state\x18\x01 \x01(\x0e\x32\x13.RemoteBrowserState\x12\x30\n\x0flocal_variables\x18\x02 \x01(\x0b\x32\x17.google.protobuf.Struct\x12\x18\n\x06stdout\x18\x03 \x03(\x0b\x32\x08.Content\x12\x0e\n\x06stderr\x18\x04 \x01(\t\x12\x11\n\texit_code\x18\x05 \x01(\x05"k\n\x11\x43odeRunnerRequest\x12\x13\n\x0bsource_code\x18\x01 \x01(\t\x12\x14\n\x0ctimeout_secs\x18\x02 \x01(\x05\x12\x12\n\nsession_id\x18\x03 \x01(\t\x12\x17\n\x05\x66iles\x18\x04 \x03(\x0b\x32\x08.Content"{\n\x12\x43odeRunnerResponse\x12"\n\x05state\x18\x01 \x01(\x0e\x32\x13.RemoteBrowserState\x12\x18\n\x06stdout\x18\x02 \x03(\x0b\x32\x08.Content\x12\x0e\n\x06stderr\x18\x03 \x01(\t\x12\x17\n\x05\x66iles\x18\x04 \x03(\x0b\x32\x08.Content*_\n\x0f\x43ontentMimeType\x12\x08\n\x04TEXT\x10\x00\x12\x08\n\x04JSON\x10\x01\x12\x08\n\x04HTML\x10\x02\x12\x07\n\x03PNG\x10\x03\x12\x08\n\x04JPEG\x10\x04\x12\x07\n\x03SVG\x10\x05\x12\x07\n\x03PDF\x10\x06\x12\t\n\x05LATEX\x10\x07*}\n\x12\x42rowserCommandType\x12\x08\n\x04GOTO\x10\x00\x12\r\n\tTERMINATE\x10\x01\x12\x08\n\x04WAIT\x10\x02\x12\t\n\x05\x43LICK\x10\x03\x12\x08\n\x04\x43OPY\x10\x04\x12\x08\n\x04TYPE\x10\x05\x12\x0c\n\x08SCROLL_X\x10\x06\x12\x0c\n\x08SCROLL_Y\x10\x07\x12\t\n\x05\x45NTER\x10\x08*>\n\x12RemoteBrowserState\x12\x0b\n\x07RUNNING\x10\x00\x12\x0e\n\nTERMINATED\x10\x01\x12\x0b\n\x07TIMEOUT\x10\x02\x32\xd4\x02\n\x06Runner\x12G\n\x10GetRemoteBrowser\x12\x15.RemoteBrowserRequest\x1a\x16.RemoteBrowserResponse"\x00(\x01\x30\x01\x12S\n\x14GetPlaywrightBrowser\x12\x19.PlaywrightBrowserRequest\x1a\x1a.PlaywrightBrowserResponse"\x00(\x01\x30\x01\x12l\n\x1dGetRestrictedPythonCodeRunner\x12".RestrictedPythonCodeRunnerRequest\x1a#.RestrictedPythonCodeRunnerResponse"\x00\x30\x01\x12>\n\rGetCodeRunner\x12\x12.CodeRunnerRequest\x1a\x13.CodeRunnerResponse"\x00(\x01\x30\x01\x62\x06proto3'
)

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, "runner_pb2", _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    DESCRIPTOR._options = None
    _globals["_CONTENTMIMETYPE"]._serialized_start = 2097
    _globals["_CONTENTMIMETYPE"]._serialized_end = 2192
    _globals["_BROWSERCOMMANDTYPE"]._serialized_start = 2194
    _globals["_BROWSERCOMMANDTYPE"]._serialized_end = 2319
    _globals["_REMOTEBROWSERSTATE"]._serialized_start = 2321
    _globals["_REMOTEBROWSERSTATE"]._serialized_end = 2383
    _globals["_CONTENT"]._serialized_start = 46
    _globals["_CONTENT"]._serialized_end = 106
    _globals["_BROWSERINPUT"]._serialized_start = 108
    _globals["_BROWSERINPUT"]._serialized_end = 189
    _globals["_BROWSERINITDATA"]._serialized_start = 191
    _globals["_BROWSERINITDATA"]._serialized_end = 316
    _globals["_BROWSEROUTPUT"]._serialized_start = 318
    _globals["_BROWSEROUTPUT"]._serialized_end = 360
    _globals["_BROWSERBUTTON"]._serialized_start = 362
    _globals["_BROWSERBUTTON"]._serialized_end = 409
    _globals["_BROWSERINPUTFIELD"]._serialized_start = 411
    _globals["_BROWSERINPUTFIELD"]._serialized_end = 462
    _globals["_BROWSERSELECTFIELD"]._serialized_start = 464
    _globals["_BROWSERSELECTFIELD"]._serialized_end = 516
    _globals["_BROWSERTEXTAREAFIELD"]._serialized_start = 518
    _globals["_BROWSERTEXTAREAFIELD"]._serialized_end = 572
    _globals["_BROWSERLINK"]._serialized_start = 574
    _globals["_BROWSERLINK"]._serialized_end = 632
    _globals["_BROWSERCONTENT"]._serialized_start = 635
    _globals["_BROWSERCONTENT"]._serialized_end = 920
    _globals["_REMOTEBROWSERREQUEST"]._serialized_start = 922
    _globals["_REMOTEBROWSERREQUEST"]._serialized_end = 1011
    _globals["_REMOTEBROWSERSESSION"]._serialized_start = 1013
    _globals["_REMOTEBROWSERSESSION"]._serialized_end = 1073
    _globals["_REMOTEBROWSERRESPONSE"]._serialized_start = 1075
    _globals["_REMOTEBROWSERRESPONSE"]._serialized_end = 1174
    _globals["_PLAYWRIGHTBROWSERREQUEST"]._serialized_start = 1177
    _globals["_PLAYWRIGHTBROWSERREQUEST"]._serialized_end = 1307
    _globals["_PLAYWRIGHTBROWSERRESPONSE"]._serialized_start = 1310
    _globals["_PLAYWRIGHTBROWSERRESPONSE"]._serialized_end = 1495
    _globals["_PYTHONCODERUNNERFILE"]._serialized_start = 1497
    _globals["_PYTHONCODERUNNERFILE"]._serialized_end = 1550
    _globals["_RESTRICTEDPYTHONCODERUNNERREQUEST"]._serialized_start = 1552
    _globals["_RESTRICTEDPYTHONCODERUNNERREQUEST"]._serialized_end = 1675
    _globals["_RESTRICTEDPYTHONCODERUNNERRESPONSE"]._serialized_start = 1678
    _globals["_RESTRICTEDPYTHONCODERUNNERRESPONSE"]._serialized_end = 1861
    _globals["_CODERUNNERREQUEST"]._serialized_start = 1863
    _globals["_CODERUNNERREQUEST"]._serialized_end = 1970
    _globals["_CODERUNNERRESPONSE"]._serialized_start = 1972
    _globals["_CODERUNNERRESPONSE"]._serialized_end = 2095
    _globals["_RUNNER"]._serialized_start = 2386
    _globals["_RUNNER"]._serialized_end = 2726
# @@protoc_insertion_point(module_scope)
