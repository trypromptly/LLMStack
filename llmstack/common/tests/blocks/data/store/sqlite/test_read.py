import unittest
from llmstack.common.blocks.data.store.sqlite import SQLiteConfiguration

from llmstack.common.blocks.data.store.sqlite.read import SQLiteReader, SQLiteReaderInput


class SqliteReadTest(unittest.TestCase):
    def test_read(self):
        sample_db = f"{'/'.join((__file__.split('/')[:-1]))}/sample.db"
        response = SQLiteReader().process(
            SQLiteReaderInput(
                sql='SELECT * FROM users'),
            SQLiteConfiguration(
                dbpath=sample_db))
        self.assertEquals(len(response.documents), 1)
