import ast
import logging
import re
from typing import List
from typing import Optional
from typing import Union

from llmstack.common.blocks.base.processor import BaseConfiguration
from llmstack.common.blocks.base.processor import BaseConfigurationType
from llmstack.common.blocks.base.processor import BaseInput
from llmstack.common.blocks.base.processor import BaseInputType
from llmstack.common.blocks.base.processor import BaseOutput
from llmstack.common.blocks.base.processor import BaseOutputType
from llmstack.common.blocks.base.processor import ProcessorInterface


logger = logging.getLogger(__name__)


class PythonCodeExecutorProcessorInputDict(BaseInput):
    key: str
    value: Union[
        str, int, float, bool, List[str],
        List[int], List[float], List[bool],
    ]


class PythonCodeExecutorProcessorInput(BaseInput):
    inputs: List[PythonCodeExecutorProcessorInputDict]
    function_name: str


class PythonCodeExecutorProcessorOutput(BaseOutput):
    output: str


class PythonCodeExecutorProcessorConfiguration(BaseConfiguration):
    python_function_code: str
    allowed_functions: Optional[List[str]] = [
        'len', 'concat', 'join', 'split', 'lower', 'upper', 'strip', 'replace', 'startswith', 'endswith', 'find', 'rfind', 'index', 'rindex', 'count', 'isalnum', 'isalpha', 'isdigit', 'islower', 'isspace', 'istitle', 'isupper', 'ljust', 'rjust', 'center', 'zfill', 'lstrip', 'rstrip', 'partition', 'rpartition', 'capitalize', 'swapcase', 'title', 'translate', 'casefold', 'encode', 'decode', 'format', 'format_map', 'maketrans', 'expandtabs', 'strip', 'lstrip', 'rstrip', 'split', 'rsplit', 'splitlines', 'join', 'find', 'rfind', 'index', 'rindex', 'count', 'startswith', 'endswith', 'isalnum', 'isalpha', 'isdigit', 'islower', 'isspace', 'istitle', 'isupper', 'lower', 'upper', 'title', 'capitalize', 'swapcase', 'casefold', 'strip', 'lstrip', 'rstrip', 'split', 'rsplit',
        'splitlines', 'join', 'find', 'rfind', 'index', 'rindex', 'count', 'startswith', 'endswith', 'isalnum', 'isalpha', 'isdigit', 'islower', 'isspace', 'istitle', 'isupper', 'lower', 'upper', 'title', 'capitalize', 'swapcase', 'casefold', 'strip', 'lstrip', 'rstrip', 'split', 'rsplit', 'splitlines', 'join', 'find', 'rfind', 'index', 'rindex', 'count', 'startswith', 'endswith', 'isalnum', 'isalpha', 'isdigit', 'islower', 'isspace', 'istitle', 'isupper', 'lower', 'upper', 'title', 'capitalize', 'swapcase', 'casefold', 'strip', 'lstrip', 'rstrip', 'split', 'rsplit', 'splitlines', 'join', 'find', 'rfind', 'index', 'rindex', 'count', 'startswith', 'endswith', 'isalnum', 'isalpha', 'isdigit', 'islower', 'isspace', 'istitle', 'isupper', 'lower', 'upper', 'title', 'capitalize',
    ]
    allowed_keywords: Optional[List[str]] = ['def', 'return']


def is_user_input_safe(user_function, allowed_calls=[], allowed_keywords=[]):
    # Check the user input against the whitelist
    tree = ast.parse(user_function)
    for node in ast.walk(tree):
        # Check if function calls are allowed
        if isinstance(node, ast.Call) and not (isinstance(node.func, ast.Name) and node.func.id in allowed_calls):
            return False

        # Check if keywords are allowed
        if isinstance(node, ast.keyword) and node.arg not in allowed_keywords:
            return False

    # Check for disallowed import statements
    if re.search(r'\bimport\b|\bfrom\b', user_function):
        return False

    return True


class PythonCodeExecutorProcessor(ProcessorInterface[PythonCodeExecutorProcessorInput, PythonCodeExecutorProcessorOutput, PythonCodeExecutorProcessorConfiguration]):
    """
    # PythonCodeExecutorProcessor

    The `PythonCodeExecutorProcessor` is a processor that helps to execute Python code safely by limiting the allowed functions and keywords. The processor takes a Python function as input and executes it with the provided input arguments.

    ## Classes

    ### PythonCodeExecutorProcessorInputDict

    This class inherits from `BaseInput` and represents a key-value pair for the input arguments.

    Attributes:

    - `key`: A string representing the key for the input argument.
    - `value`: A value of different types (str, int, float, bool, List[str], List[int], List[float], List[bool]).

    ### PythonCodeExecutorProcessorInput

    This class inherits from `BaseInput` and represents the input for the PythonCodeExecutorProcessor.

    Attributes:

    - `inputs`: A list of `PythonCodeExecutorProcessorInputDict` objects representing the input arguments.
    - `function_name`: A string representing the name of the function to execute.

    ### PythonCodeExecutorProcessorOutput

    This class inherits from `BaseOutput` and represents the output of the PythonCodeExecutorProcessor.

    Attributes:

    - `output`: A string representing the result of the executed Python function.

    ### PythonCodeExecutorProcessorConfiguration

    This class inherits from `BaseConfiguration` and represents the configuration for the PythonCodeExecutorProcessor.

    Attributes:

    - `python_function_code`: A string containing the Python function code to execute.
    - `allowed_functions`: An optional list of allowed function names (default: a list of common string manipulation functions).
    - `allowed_keywords`: An optional list of allowed Python keywords (default: ['def', 'return']).

    ### PythonCodeExecutorProcessor

    This class inherits from `BaseProcessor` and represents the main class for the PythonCodeExecutorProcessor. It handles the execution of the provided Python function with the given input arguments and configuration.

    Methods:

    - `_process(self, input: PythonCodeExecutorProcessorInput, configuration: PythonCodeExecutorProcessorConfiguration) -> PythonCodeExecutorProcessorOutput`: Executes the provided Python function with the given input arguments and configuration, and returns the result as a `PythonCodeExecutorProcessorOutput` object.
    """

    def process(self,  input: PythonCodeExecutorProcessorInput, configuration: PythonCodeExecutorProcessorConfiguration) -> PythonCodeExecutorProcessorOutput:
        """
            Invokes the processor on the input and returns the output
        """
        if not is_user_input_safe(configuration.python_function_code, configuration.allowed_functions, configuration.allowed_keywords):
            raise Exception('User input is not safe')
        exec(configuration.python_function_code)
        user_func_name = input.function_name

        if user_func_name == '':
            raise Exception('User function name is not valid')

        function_input = {i.key: i.value for i in input.inputs}
        try:
            result = locals()[user_func_name](**function_input)
        except Exception as e:
            result = f'Exception occurred : {str(e)}'

        return PythonCodeExecutorProcessorOutput(output=result)
