---
id: promptly
title: Promptly
---

The `Promptly` provider includes processors that are high level abstractions built on top of processors/models from other providers. For example, it includes processors like `Text-Chat` built on top of OpenAI's chat completions API and includes data retrieval from vector store.

## Text-Chat

The `Text-Chat` processor is a high level abstraction built on top of OpenAI's chat completions API. It allows you to chat with an AI model using a simple prompt-response interface. It also includes data retrieval from vector store.

### Input

- `question`: The question to ask the AI model.
- `search_filters`: The search filters to use to retrieve data from the vector store as a string. It is of the format `key1 == value1 || key2 == value2` or `key1 == value1 && key2 == value2`.

### Configuration

`datasources`: List of datasource UUIDs to use to retrieve data from the vector store for the asked question. If not provided, it will not provide any context to the LLM model.

- `model`: LLM model to use for the chat.
- `system_messsage_prefix`: Prefix to use for system message to the LLM.
- `instructions`: Instructions to pass in the messages to the LLM.
- `documents_count`: Maximum number of chunks of data to retrieve from the vector store for the asked question.
- `chat_history_limit`: Maximum number of chat history messages to save in a session and pass to the LLM in the next prompt.
- `temperature`: Temperature to use for the LLM.
- `use_azure_if_available`: Use Azure's OpenAI models if a key is configured in the settings or in the organization that the user is part of.
- `chat_history_in_doc_search`: Include chat history in the search query to the vector store.

### Output

- `answer`: The answer from the AI model.

## Datasource search

The `Datasource search` processor allows you to search for data in the vector store using a simple prompt-response interface and optional metadata filtering.

### Input

- `query`: The query to search in the vector store.

### Configuration

- `datasources`: List of datasource UUIDs to use to retrieve data from the vector store for the asked query.
- `document_limit`: Maximum number of documents to retrieve from the vector store for the asked query.
- `search_filters`: The search filters to use to retrieve data from the vector store as a string. It is of the format `key1 == value1 || key2 == value2` or `key1 == value1 && key2 == value2`.

### Output

- `answers`: Array of documents matching the query.
- `answers_text`: Array of documents matching the query as a single blob of text.

## URL Extractor

Extracts text from a URL.

### Input

- `url`: The URL to extract text from.
- `query`: An optional query to semantic search in the extracted text.

### Configuration

- `document_limit`: Maximum number of documents to retrieve from the vector store for the asked query.
- `text_chunk_size`: Chunk size of document to use for semantic search.

### Output

- `text`: The extracted text from the URL.

## File Extractor

Extracts text from a file.

### Input

- `file`: The file to extract text from.
- `file_data`: Alternative to `file` input. The base64 encoded file data to extract text from. This is useful when you want to extract text from a file that is uploaded via API or when wiring processors together.
- `query`: An optional query to semantic search in the extracted text.

### Configuration

- `document_limit`: Maximum number of documents to retrieve from the vector store for the asked query.
- `text_chunk_size`: Chunk size of document to use for semantic search.

### Output

- `text`: The extracted text from the file.
