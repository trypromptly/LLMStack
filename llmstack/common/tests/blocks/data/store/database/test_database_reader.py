import unittest

from llmstack.common.blocks.data.store.database.database_reader import (
    DatabaseReader,
    DatabaseReaderInput,
)
from llmstack.common.blocks.data.store.database.mysql import MySQLConfiguration
from llmstack.common.blocks.data.store.database.postgresql import PostgresConfiguration
from llmstack.common.blocks.data.store.database.sqlite import SQLiteConfiguration


class MySQLReadTest(unittest.TestCase):
    def test_read(self):
        configuration = MySQLConfiguration(
            user="root",
            password="",
            host="localhost",
            port=3306,
            dbname="usersdb",
        )
        reader_input = DatabaseReaderInput(
            sql="SELECT * FROM users",
        )

        response = DatabaseReader().process(
            reader_input,
            configuration,
        )

        self.assertEqual(len(response.documents), 1)


class PostgresReadTest(unittest.TestCase):
    def test_read(self):
        configuration = PostgresConfiguration(
            user="root",
            password="",
            host="localhost",
            port=5432,
            dbname="usersdb",
        )
        reader_input = DatabaseReaderInput(
            sql="SELECT * FROM users",
        )

        response = DatabaseReader().process(
            reader_input,
            configuration,
        )

        self.assertEqual(len(response.documents), 1)


class SqliteReadTest(unittest.TestCase):
    def test_read(self):
        sample_db = f"{'/'.join((__file__.split('/')[:-1]))}/sample.db"
        response = DatabaseReader().process(
            DatabaseReaderInput(
                sql="SELECT * FROM users",
            ),
            SQLiteConfiguration(
                dbpath=sample_db,
            ),
        )
        self.assertEqual(len(response.documents), 1)
