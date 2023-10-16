---
id: azure
title: Azure
---

The `Azure` provider includes processors that correspond to models from [Azure's OpenAI service](https://azure.microsoft.com/en-us/products/ai-services/openai-service).

## Azure ChatGPT

### Input

- `prompt`: The prompt to ask the ChatGPT model.
- `search_filters`: (Optional) The search filters to use to retrieve data from a vector store as a string. It is of the format `key1 == value1 || key2 == value2` or `key1 == value1 && key2 == value2`.

### Configuration

`datasources`: (Optional) List of datasource UUIDs to use to retrieve data from the vector store for the asked question. If not provided, it will not provide any context to the ChatGPT model.

- `model`: (Optional) ChatGPT model to use for the chat. Default: `ChatCompletionsModel.GPT_4`.
- `system_message_prefix`: (Optional) Prefix to use for system message to the ChatGPT. Default: `None`.
- `instructions`: (Optional) Instructions to pass in the messages to the ChatGPT. Default: `None`.
- `documents_count`: (Optional) Maximum number of chunks of data to retrieve from the vector store for the asked question. Default: `10`.

- `chat_history_limit`: (Optional) Maximum number of chat history messages to save in a session and pass to the ChatGPT in the next prompt. Default: `100`.
- `temperature`: (Optional) Temperature to use for the ChatGPT. Default: `0.7`.
- `use_azure_if_available`: (Optional) Use Azure's ChatGPT models if a key is configured in the settings or in the organization that the user is part of. Default: `True`.
- `chat_history_in_doc_search`: (Optional) Include chat history in the search query to the vector store. Default: `False`.
- `show_citations`: (Optional) Cites the sources used to generate the answer. Default: `False`.
- `citation_instructions`: (Optional) Instructions to pass in the messages to the ChatGPT for citations. This can be used to control how the citations are generated and presented. Default: `None`.

### Output

- `answer`: The answer from the ChatGPT model.
- `citations`: (Optional) The list citations for the answer.
