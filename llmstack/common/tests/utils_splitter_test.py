import unittest

from llmstack.common.utils.splitter import CSVTextSplitter

# Unitest for CSVTextSplitter


class TestCSVTextSplitter(unittest.TestCase):
    def test_csv_splitter(self):
        csv_data = """
        a,b,c,d,e
        1,2,3,4,"Foo"
        5,6,7,8,"Bar"
        9,10,11,12,"Baz"
        """
        output = CSVTextSplitter(
            chunk_size=100, chunk_overlap=1,
            length_function=CSVTextSplitter.num_tokens_from_string_using_tiktoken,
        ).split_text(csv_data)
        print(len(output))
