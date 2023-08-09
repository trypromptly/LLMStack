# Tests for all processor implementations should be written here.
import json
import os

from processors.providers.cohere.generate import Generate
from processors.providers.openai.completions import Completions

# Basic test for cohere processor


def test_cohere_generate():
    processor = Generate({}, {}, {})
    assert Generate.name() == 'cohere/generate'

    response = processor.process(
        {'prompt': 'Hello world!', '_env': {'cohere_api_key': os.getenv('COHERE_API_KEY', 'Qg8PfTe4Apd7spTLkaxIbO4ynLX4Xx6TfhpI5Zno')}},
    )
    assert response.choices is not None
    assert len(response.choices) > 0
    assert response._api_response is not None
    output_schema = """
        {
    "title": "GenerateOutput",
    "description": "This is Base Schema model for all API processor schemas",
    "type": "object",
    "properties": {
        "choices": {
        "title": "Choices",
        "default": [],
        "widget": "output_text",
        "type": "array",
        "items": {
            "type": "string"
        }
        }
    }
    }
    """

    assert json.loads(
        (response.schema_json(indent=2)),
    ) == json.loads(output_schema)

# Basic test for openai processor


def test_openai_completions():
    processor = Completions({}, {}, {})
    assert Completions.name() == 'openai/completions'


if __name__ == '__main__':
    test_cohere_generate()
