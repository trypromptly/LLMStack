import logging
import signal

from asgiref.sync import async_to_sync
from pydantic import Field

from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface, ApiProcessorSchema

logger = logging.getLogger(__name__)


class CodeInterpreterInput(ApiProcessorSchema):
    code: str = Field(description='The code to run')
    language: str = Field(
        default='python', description='The language of the code')


class CodeInterpreterOutput(ApiProcessorSchema):
    output: str = Field(..., description='The output of the code')


class CodeInterpreterConfiguration(ApiProcessorSchema):
    pass


class CodeInterpreterProcessor(
        ApiProcessorInterface[CodeInterpreterInput, CodeInterpreterOutput, CodeInterpreterConfiguration]):
    @staticmethod
    def name() -> str:
        return 'Code Interpreter'

    @staticmethod
    def slug() -> str:
        return 'code_interpreter'

    @staticmethod
    def description() -> str:
        return 'Runs code in a sandboxed environment'

    @staticmethod
    def provider_slug() -> str:
        return 'promptly'

    @staticmethod
    def tool_only() -> bool:
        return True

    def process(self) -> dict:
        output_stream = self._output_stream
        code = self._input.code

        # Run the input code in a sandboxed subprocess environment and return
        # the output
        if not self._input.language == 'python':
            raise Exception('Invalid language')

        import subprocess
        import sys
        import os
        import tempfile
        import shutil
        import time

        # Create a temporary directory to store the code
        temp_dir = tempfile.mkdtemp()
        # Create a temporary file to store the code
        temp_file = tempfile.NamedTemporaryFile(
            dir=temp_dir, delete=False)
        # Write the code to the temporary file
        temp_file.write(code.encode('utf-8'))
        temp_file.close()

        # Run the code in a subprocess
        process = subprocess.Popen(
            [sys.executable, temp_file.name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
        )

        # Wait for the process to finish or timeout
        timeout = 5
        start_time = time.time()
        while process.poll() is None:
            time.sleep(0.1)
            if time.time() - start_time > timeout:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                raise Exception('Code timed out')

        # Get the output
        output, error = process.communicate()
        output = output.decode('utf-8')
        error = error.decode('utf-8')

        # Delete the temporary directory
        shutil.rmtree(temp_dir)

        # Send the output
        async_to_sync(output_stream.write)(
            CodeInterpreterOutput(output=output))

        if error:
            raise Exception(error)

        output = output_stream.finalize()
        return output
