import os
import unittest

from common.promptly.vectorstore import Document
from common.promptly.vectorstore import DocumentQuery
from common.promptly.vectorstore.chroma import Chroma
from common.promptly.vectorstore.weaviate import Weaviate


class ChromaTest(unittest.TestCase):
    TEST_INDEX = 'test_index'

    def setUp(self):
        self.chroma_handle = Chroma()
        self.chroma_handle.create_index(
            schema=None, index_name=self.TEST_INDEX,
        )

    def test_client_creation(self):
        self.assertIsNotNone(self.chroma_handle.client)

    def test_add_document(self):
        result = self.chroma_handle.add_text(
            self.TEST_INDEX, Document(
            'content', 'Test content', {'source': 'test'},
            ),
        )
        self.assertIsNotNone(result)

    def test_add_query_document(self):
        result = self.chroma_handle.add_text(
            self.TEST_INDEX, Document(
            'content', 'Test content', {'source': 'test'},
            ),
        )
        self.assertIsNotNone(result)
        result = self.chroma_handle.similarity_search(
            self.TEST_INDEX, DocumentQuery('Test content', 'content', 1, {}),
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].page_content, 'Test content')
        self.assertDictEqual(result[0].metadata, {'source': 'test'})

    def test_add_delete_document(self):
        result = self.chroma_handle.add_text(
            self.TEST_INDEX, Document(
            'content', 'Test content', {'source': 'test'},
            ),
        )
        self.assertIsNotNone(result)
        self.chroma_handle.delete_document(result, index_name=self.TEST_INDEX)
        self.assertListEqual(
            self.chroma_handle.client.get_collection(
            self.TEST_INDEX,
            ).get(result)['ids'], [],
        )


class WeaviateTest(unittest.TestCase):
    TEST_INDEX = 'test_index'
    TEST_SCHEMA = """
    {"classes": [{"class": "test_index", "description": "Text data source", "vectorizer": "text2vec-openai", "moduleConfig": {"text2vec-openai": {"model": "ada", "type": "text"}}, "properties": [{"name": "content", "dataType": ["text"], "description": "Text",
        "moduleConfig": {"text2vec-openai": {"skip": false, "vectorizePropertyName": false}}}, {"name": "source", "dataType": ["string"], "description": "Document source"}, {"name": "metadata", "dataType": ["string[]"], "description": "Document metadata"}]}]}
    """

    def setUp(self):
        self.weaviate_handle = Weaviate(
            url=os.environ.get('WEAVIATE_URL'), openai_key=os.environ.get('OPENAI_API_KEY'),
        )

        self.weaviate_handle.create_index(
            schema=self.TEST_SCHEMA, index_name=self.TEST_INDEX,
        )

    def tearDown(self):
        self.weaviate_handle.delete_index(self.TEST_INDEX)

    def test_client_creation(self):
        self.assertIsNotNone(self.weaviate_handle.client)

    def test_add_query_document(self):
        result = self.weaviate_handle.add_text(
            self.TEST_INDEX, Document(
            'content', 'Test content', {'source': 'test'},
            ),
        )
        self.assertIsNotNone(result)
        result = self.weaviate_handle.similarity_search(
            self.TEST_INDEX.capitalize(), DocumentQuery('Test content', 'content', 1, {'additional_properties': ['source']}),
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].page_content, 'Test content')
        self.assertEqual(result[0].metadata['source'], 'test')
        self.weaviate_handle.delete_document(
            result[0].metadata['id'], index_name=self.TEST_INDEX,
        )

    def test_batch_add_query_document(self):
        result = self.weaviate_handle.add_texts(
            self.TEST_INDEX, [
                Document(
                'content', 'Test content', {'source': 'test'},
                ), Document(
                'content', 'Test1 content', {'source': 'test1'},
                ),
            ],
        )
        self.assertIsNotNone(result)
        result = self.weaviate_handle.similarity_search(
            self.TEST_INDEX.capitalize(), DocumentQuery('Test content', 'content', 1, {'additional_properties': ['source']}),
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].page_content, 'Test content')
        self.assertEqual(result[0].metadata['source'], 'test')
        self.weaviate_handle.delete_document(
            result[0].metadata['id'], index_name=self.TEST_INDEX,
        )


if __name__ == '__main__':
    unittest.main()
