import unittest

from common.utils.splitter import CSVTextSplitter
from common.utils.splitter import SpacyTextSplitter


class TestSplitter(unittest.TestCase):

    def test_csv_splitter_valid(self):
        splitter = CSVTextSplitter(chunk_size=10, chunk_overlap=5)
        text = 'name,age\nJohn,25\nJane,26\nJack,27\nJill,28\n'
        chunks = splitter.split_text(text)
        assert len(chunks) == 4


    def test_spacy_splitter_valid(self):
        splitter = SpacyTextSplitter(chunk_size=15, chunk_overlap=10)
        text = """This is a sentence. This is another sentence. This is a third sentence."""
        chunks = splitter.split_text(text)
        assert len(chunks) == 2