---
id: promptly
title: Promptly
---

The `Promptly` provider includes processors that are high level abstractions built on top of processors/models from other providers. For example, it includes processors like `Text-Chat` built on top of other LLM chat models and natively implements a RAG pipeline.

## Text-Chat

The `Text-Chat` processor is a high level abstraction built on top of other LLM chat models and natively implements a RAG pipeline. It is a simple prompt-response interface that allows you to chat with the AI model. It also supports chat history and context from the vector store.

### Input

- `question`: The question to ask the AI model.
- `search_filters`: The search filters to use to retrieve data from the vector store as a string. It is of the format `key1 == value1 || key2 == value2` or `key1 == value1 && key2 == value2`.

### Configuration

- `model`: LLM model to use for the chat.
- `datasources`: List of datasource UUIDs to use to retrieve data from the vector store for the asked question as part of the RAG pipeline. If not provided, the processor will behave like a simple chatbot without your data.
- `system_messsage_prefix`: System message that defines the character of the assistant.
- `instructions`: Instructions to pass in the messages to the LLM.
- `show_citations`: Cites the sources used to generate the answer.
- `citation_instructions`: Instructions to pass in the messages to the LLM for citations. This can be used to control how the citations are generated and presented.
- `k`: Maximum number of chunks of data to retrieve from the vector store for the asked question.
- `chat_history_limit`: Maximum number of chat history messages to save in a session and pass to the LLM in the next prompt.
- `temperature`: Temperature to use for the LLM.
- `use_azure_if_available`: Use Azure's OpenAI models if a key is configured in the settings or in the organization that the user is part of.
- `use_localai_if_available`: Use LocalAI models if a LocalAI key and url are configured in the settings.
- `chat_history_in_doc_search`: Include chat history in the search query to the vector store.
- `hybrid_semantic_search_ratio`: Ratio of semantic search results to use for hybrid search. This will use a combination of semantic search and keyword search to retrieve data from the vector store.
- `seed`: Seed to use with the model. This is useful when you want to get the same answer for the same question.

### Output

- `answer`: The answer from the AI model.
- `citations`: The list citations for the answer.
  - `text`: The text of the citation.
  - `source`: The source of the citation, for example, the url of the document.

## Datasource search

The `Datasource search` processor allows you to search for data in the default vector store using a simple prompt-response interface and optional metadata filtering.

### Input

- `query`: The query to search in the vector store.

### Configuration

- `datasources`: List of datasource UUIDs to use to retrieve data from the vector store for the asked query.
- `document_limit`: Maximum number of documents to retrieve from the vector store for the asked query.
- `search_filters`: The search filters to use to retrieve data from the vector store as a string. It is of the format `key1 == value1 || key2 == value2` or `key1 == value1 && key2 == value2`.
- `hybrid_semantic_search_ratio`: Ratio of semantic search to hybrid search. This will use a combination of semantic search and keyword search to retrieve data from the vector store.

### Output

- `answers_text`: Stitched text of all the documents matching the query along with their source info.
- `answers`: Array of documents matching the query.
  - `content`: The content of the document.
  - `source`: The source of the document, for example, the url of the document.
  - `metadata`: The metadata of the document.
  - `additional_properties`: Additional properties of the document.

## HTTP API

The `HTTP API` processor allows you to make HTTP requests to any API. It supports GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS, and TRACE methods. It also supports basic authentication and custom headers.

### Input

### Configuration

### Output

## Web Search

### Input

### Configuration

### Output

## Static Web Browser

### Input

### Configuration

### Output

## Web Browser

### Input

### Configuration

### Output

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
