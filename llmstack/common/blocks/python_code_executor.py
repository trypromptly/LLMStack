import importlib
import logging
from datetime import datetime
from typing import List, Optional

from RestrictedPython import compile_restricted
from RestrictedPython.Guards import (
    guarded_iter_unpack_sequence,
    guarded_unpack_sequence,
    safe_builtins,
)
from RestrictedPython.transformer import IOPERATOR_TO_STR

from llmstack.common.blocks.base.processor import (
    BaseConfiguration,
    BaseInput,
    BaseOutput,
    ProcessorInterface,
)

logger = logging.getLogger(__name__)


class CustomPrint(object):
    def __init__(self):
        self.enabled = True
        self.lines = []

    def write(self, text):
        if self.enabled:
            if text and text.strip():
                log_line = "[{0}] {1}".format(
                    datetime.utcnow().isoformat(),
                    text,
                )
                self.lines.append(log_line)

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def __call__(self, *args):
        return self

    def _call_print(self, *objects, **kwargs):
        print(*objects, file=self)


class PythonCodeExecutorProcessorInput(BaseInput):
    code: str


class PythonCodeExecutorProcessorOutput(BaseOutput):
    output: Optional[str]
    logs: Optional[List[str]]


class PythonCodeExecutorProcessorConfiguration(BaseConfiguration):
    allowed_modules: Optional[List[str]]
    allowed_builtins: Optional[List[str]]
    result_variable: Optional[str] = "result"


class PythonCodeExecutorProcessor(
    ProcessorInterface[
        PythonCodeExecutorProcessorInput,
        PythonCodeExecutorProcessorOutput,
        PythonCodeExecutorProcessorConfiguration,
    ],
):
    @staticmethod
    def custom_write(obj):
        """
        Custom hooks which controls the way objects/lists/tuples/dicts behave in
        RestrictedPython
        """
        return obj

    @staticmethod
    def custom_get_item(obj, key):
        return obj[key]

    @staticmethod
    def custom_get_iter(obj):
        return iter(obj)

    @staticmethod
    def custom_inplacevar(op, x, y):
        if op not in IOPERATOR_TO_STR.values():
            raise Exception(
                "'{} is not supported inplace variable'".format(op),
            )
        glb = {"x": x, "y": y}
        exec("x" + op + "y", glb)
        return glb["x"]

    def process(
        self,
        input: PythonCodeExecutorProcessorInput,
        configuration: PythonCodeExecutorProcessorConfiguration,
    ) -> PythonCodeExecutorProcessorOutput:
        allowed_modules = {}
        for module in configuration.allowed_modules or []:
            allowed_modules[module] = None

        allowed_builtins = safe_builtins.copy()
        for builtin in configuration.allowed_builtins or []:
            allowed_builtins += (builtin,)

        def custom_import(
            self,
            name,
            globals=None,
            locals=None,
            fromlist=(),
            level=0,
        ):
            if name in allowed_modules:
                m = importlib.import_module(name)
                return m

            raise Exception(
                "'{0}' is not configured as a supported import module".format(name),
            )

        custom_print = CustomPrint()
        code = compile_restricted(input.code, "<string>", "exec")

        builtins = allowed_builtins.copy()

        builtins["_write_"] = self.custom_write
        builtins["_print_"] = custom_print
        builtins["__import__"] = custom_import
        builtins["_getitem_"] = self.custom_get_item
        builtins["_getiter_"] = self.custom_get_iter
        builtins["_unpack_sequence_"] = guarded_unpack_sequence
        builtins["_iter_unpack_sequence_"] = guarded_iter_unpack_sequence
        builtins["_inplacevar_"] = self.custom_inplacevar
        builtins["_getattr_"] = getattr
        builtins["getattr"] = getattr
        builtins["_setattr_"] = setattr
        builtins["setattr"] = setattr

        restricted_globals = dict(__builtins__=builtins)

        code_exec_result = {configuration.result_variable: None}
        exec(code, restricted_globals, code_exec_result)
        result = code_exec_result.get(configuration.result_variable)
        logs = custom_print.lines

        return PythonCodeExecutorProcessorOutput(output=result, logs=logs)
