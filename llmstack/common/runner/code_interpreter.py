import asyncio
import logging
import time
from concurrent import futures
from typing import Iterator

import matplotlib.pyplot as plt
from google.protobuf.json_format import MessageToDict, ParseDict
from google.protobuf.struct_pb2 import Struct, Value
from grpc import ServicerContext
from RestrictedPython import compile_restricted
from RestrictedPython.Guards import (
    guarded_iter_unpack_sequence,
    guarded_unpack_sequence,
    safe_builtins,
)
from RestrictedPython.transformer import IOPERATOR_TO_STR

from llmstack.common.runner.proto.runner_pb2 import (
    Content,
    ContentMimeType,
    RemoteBrowserState,
    RestrictedPythonCodeRunnerRequest,
    RestrictedPythonCodeRunnerResponse,
)

logger = logging.getLogger(__name__)


class CodeInterpreter:
    def get_restricted_python_code_runner(
        self, request: RestrictedPythonCodeRunnerRequest, context: ServicerContext
    ) -> Iterator[RestrictedPythonCodeRunnerResponse]:
        class CustomPrint(object):
            def __init__(self):
                self.enabled = True
                self.lines = []

            def write(self, text):
                if self.enabled:
                    if text and text.strip():
                        log_line = "{0}".format(text)
                        self.lines.append(
                            (
                                time.time(),
                                Content(data=bytes(log_line.encode("utf-8")), mime_type=ContentMimeType.TEXT),
                            )
                        )

            def enable(self):
                self.enabled = True

            def disable(self):
                self.enabled = False

            def __call__(self, *args):
                return self

            def _call_print(self, *objects, **kwargs):
                print(*objects, file=self)

        def custom_write(obj):
            """
            Custom hooks which controls the way objects/lists/tuples/dicts behave in
            RestrictedPython
            """
            return obj

        def custom_get_item(obj, key):
            return obj[key]

        def custom_get_iter(obj):
            return iter(obj)

        def custom_inplacevar(op, x, y):
            if op not in IOPERATOR_TO_STR.values():
                raise Exception("'{} is not supported inplace variable'".format(op))
            glb = {"x": x, "y": y}
            exec("x" + op + "y", glb)
            return glb["x"]

        async def execute_restricted_code(source_code, input_data={}):
            errors = None

            allowed_builtins = safe_builtins.copy()

            for builtin in []:
                allowed_builtins += (builtin,)

            mathplot_lib_display = []

            def custom_pyplot_show():
                import io

                from matplotlib.backends.backend_agg import (
                    FigureCanvasAgg as FigureCanvas,
                )

                # Save the current figure's buffer
                buf = io.BytesIO()

                # Use the current figure or create a new one
                fig = plt.gcf()

                # Create a canvas from the figure
                canvas = FigureCanvas(fig)

                # Draw the canvas and cache the renderer
                canvas.draw()

                # Save the figure to the buffer in PNG format
                fig.savefig(buf, format="png")

                # Release resources held by the figure
                plt.close(fig)

                # Rewind the buffer to start
                buf.seek(0)

                mathplot_lib_display.append((time.time(), Content(data=buf.read(), mime_type=ContentMimeType.PNG)))

                # Cleanup by closing the buffer
                buf.close()

            def custom_import(name, globals=None, locals=None, fromlist=(), level=0):
                unsafe_modules = [
                    "os",
                    "sys",
                    "subprocess",
                    "shutil",
                    "importlib",
                    "imp",
                    "importlib",
                    "importlib.util",
                    "socket",
                ]
                module = __import__(name, globals, locals, fromlist, level)
                if module.__name__ == "matplotlib":
                    pyplot_attr = getattr(module, "pyplot")
                    if pyplot_attr and hasattr(pyplot_attr, "show"):
                        # Override pyplot.show() to route to our custom show function
                        pyplot_attr.show = custom_pyplot_show

                elif module.__name__ in unsafe_modules:
                    raise Exception("Module {} is not allowed".format(module.__name__))

                if fromlist:
                    safe_attrs = {attr: getattr(module, attr) for attr in fromlist}
                    if len(safe_attrs):
                        return type("RestrictedModule", (object,), safe_attrs)
                else:
                    return module

            custom_print = CustomPrint()
            code = compile_restricted(source_code, "<string>", "exec")
            builtins = allowed_builtins.copy()

            builtins["_write_"] = custom_write
            builtins["_print_"] = custom_print
            builtins["__import__"] = custom_import
            builtins["_getitem_"] = custom_get_item
            builtins["_getiter_"] = custom_get_iter
            builtins["_unpack_sequence_"] = guarded_unpack_sequence
            builtins["_iter_unpack_sequence_"] = guarded_iter_unpack_sequence
            builtins["_inplacevar_"] = custom_inplacevar
            builtins["_getattr_"] = getattr
            builtins["getattr"] = getattr
            builtins["_setattr_"] = setattr
            builtins["setattr"] = setattr

            restricted_globals = dict(__builtins__=builtins)
            local_variables = {**input_data}
            try:
                exec(code, restricted_globals, local_variables)
            except Exception as e:
                errors = f"error: {e}"

            local_variables = {
                k: v
                for k, v in local_variables.items()
                if isinstance(v, (int, float, str, bool, list, dict, tuple, type(None), Value, Struct))
            }
            # Return the result and any printed output
            return (
                local_variables,
                [x[1] for x in sorted(custom_print.lines + mathplot_lib_display, key=lambda x: x[0])],
                errors,
            )

        yield RestrictedPythonCodeRunnerResponse(state=RemoteBrowserState.RUNNING)

        with futures.ThreadPoolExecutor() as executor:

            def run_async_code(loop):
                asyncio.set_event_loop(loop)
                return loop.run_until_complete(
                    execute_restricted_code(
                        request.source_code, MessageToDict(request.input_data) if request.input_data else {}
                    )
                )

            # Create a new event loop that will be run in a separate thread
            new_loop = asyncio.new_event_loop()
            # Submit the function to the executor and get a Future object
            future = executor.submit(run_async_code, new_loop)
            # Wait for the future to complete and get the return value
            try:
                result, stdout, stderr = future.result(
                    timeout=min(request.timeout_secs if request.timeout_secs else 30, 30)
                )

            except Exception as e:
                logger.error(e)
                result, stdout, stderr = None, [], str(e)

        response = RestrictedPythonCodeRunnerResponse(
            exit_code=0,
            stdout=stdout,
            stderr=stderr,
            local_variables=(
                ParseDict(result, Struct())
                if (result and isinstance(result, dict) and len(result.keys()) > 0)
                else None
            ),
            state=RemoteBrowserState.TERMINATED,
        )

        yield response
