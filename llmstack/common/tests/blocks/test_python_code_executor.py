import unittest
from llmstack.common.blocks.python_code_executor import PythonCodeExecutorProcessor, PythonCodeExecutorProcessorInput, PythonCodeExecutorProcessorConfiguration


class PythonCodeExecutorTestCase(unittest.TestCase):
    def test_valid_python_code_executor(self):
        code = """result = 2 + 2\nprint(result)"""
        result = PythonCodeExecutorProcessor(
        ).process(
            input=PythonCodeExecutorProcessorInput(code=code),
            configuration=PythonCodeExecutorProcessorConfiguration())
        self.assertEqual(result.output, "4")
        self.assertTrue(result.logs[0].endswith("4"))


if __name__ == '__main__':
    unittest.main()
