---
id: azure
title: Azure
---

The `Azure` provider includes processors that correspond to models from [Azure's OpenAI service](https://azure.microsoft.com/en-us/products/ai-services/openai-service)

## ChatGPT

### Input

- `prompt`: The prompt to ask the ChatGPT model.
- `search_filters`: The search filters to use to retrieve data from a vector store as a string. It is of the format `key1 == value1 || key2 == value2` or `key1 == value1 && key2 == value2`.

### Configuration

`datasources`: List of datasource UUIDs to use to retrieve data from the vector store for the asked question. If not provided, it will not provide any context to the ChatGPT model.

- `model`: ChatGPT model to use for the chat.
- `system_messsage_prefix`: Prefix to use for system message to the ChatGPT.
- `instructions`: Instructions to pass in the messages to the ChatGPT.
- `documents_count`: Maximum number of chunks of data to retrieve from the vector store for the asked question.
- `chat_history_limit`: Maximum number of chat history messages to save in a session and pass to the ChatGPT in the next prompt.
- `temperature`: Temperature to use for the ChatGPT.
- `use_azure_if_available`: Use Azure's ChatGPT models if a key is configured in the settings or in the organization that the user is part of.
- `chat_history_in_doc_search`: Include chat history in the search query to the vector store.
- `show_citations`: Cites the sources used to generate the answer.
- `citation_instructions`: Instructions to pass in the messages to the ChatGPT for citations. This can be used to control how the citations are generated and presented.

### Output

- `answer`: The answer from the ChatGPT model.
- `citations`: The list citations for the answer.

Please note that the Azure OpenAI service is still under development and may not yet be available to all users.