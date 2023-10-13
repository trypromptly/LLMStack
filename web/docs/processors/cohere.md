---
id: cohere
title: Cohere
---

The `Cohere` provider includes processors for models from [Cohere](https://cohere.com).

## Generate

### Input

- `prompt`: The prompt to ask the Cohere Generate model.
- `search_filters`: The search filters to use to retrieve data from a vector store as a string. It is of the format `key1 == value1 || key2 == value2` or `key1 == value1 && key2 == value2`.

### Configuration

`datasources`: List of datasource UUIDs to use to retrieve data from the vector store for the asked question. If not provided, it will not provide any context to the Cohere Generate model.

- `model`: Cohere Generate model to use.
- `temperature`: Temperature to use for the Cohere Generate model.
- `max_tokens`: Maximum number of tokens to generate.

### Output

- `text`: The generated text from the Cohere Generate model.
