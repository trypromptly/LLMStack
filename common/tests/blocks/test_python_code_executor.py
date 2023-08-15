import unittest 
from common.blocks.python_code_executor import PythonCodeExecutorProcessor, PythonCodeExecutorProcessorInput, PythonCodeExecutorProcessorConfiguration

class PythonCodeExecutorTestCase(unittest.TestCase):
    def test_valid_python_code_executor(self):
        code = """def python_code_executor_transform(**kwargs):
                    return kwargs['data']
               """
        result = PythonCodeExecutorProcessor(
        ).process(
            input=PythonCodeExecutorProcessorInput(**{'inputs': [{'key': 'data', 'value': 'test'}], 'function_name': 'python_code_executor_transform'}), 
            configuration=PythonCodeExecutorProcessorConfiguration(**{
            'python_function_code': code,
            }))

        self.assertEqual(result.output, 'test')
    
if __name__ == '__main__':
    unittest.main()