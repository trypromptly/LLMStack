---
id: google
title: Google
---

The `Google` provider includes processors for PaLM2 models from [Google's Vertex AI](https://cloud.google.com/vertex-ai).

## PaLM2 for Chat

### Input

- `prompt`: The prompt to ask the PaLM2 model.
- `search_filters`: The search filters to use to retrieve data from a vector store as a string. It is of the format `key1 == value1 || key2 == value2` or `key1 == value1 && key2 == value2`.

### Configuration

`datasources`: List of datasource UUIDs to use to retrieve data from the vector store for the asked question. If not provided, it will not provide any context to the PaLM2 model.

- `model`: PaLM2 model to use for the chat.
- `system_messsage_prefix`: Prefix to use for system message to the PaLM2.
- `instructions`: Instructions to pass in the messages to the PaLM2.
- `documents_count`: Maximum number of chunks of data to retrieve from the vector store for the asked question.
- `chat_history_limit`: Maximum number of chat history messages to save in a session and pass to the PaLM2 in the next prompt.
- `temperature`: Temperature to use for the PaLM2.
- `use_azure_if_available`: Use Azure's PaLM2 models if a key is configured in the settings or in the organization that the user is part of.
- `chat_history_in_doc_search`: Include chat history in the search query to the vector store.
- `show_citations`: Cites the sources used to generate the answer.
- `citation_instructions`: Instructions to pass in the messages to the PaLM2 for citations. This can be used to control how the citations are generated and presented.

### Output

- `answer`: The answer from the PaLM2 model.
- `citations`: The list citations for the answer.

## PaLM2 for Text

### Input

- `prompt`: The prompt to give to the PaLM2 model.
- `search_filters`: The search filters to use to retrieve data from a vector store as a string. It is of the format `key1 == value1 || key2 == value2` or `key1 == value1 && key2 == value2`.

### Configuration

`datasources`: List of datasource UUIDs to use to retrieve data from the vector store for the asked question. If not provided, it will not provide any context to the PaLM2 model.

- `model`: PaLM2 model to use.
- `temperature`: Temperature to use for the PaLM2.
- `max_tokens`: Maximum number of tokens to generate.

### Output

- `text`: The generated text from the PaLM2 model.
