---
id: promptly
title: Promptly
---

:::info[`provider_slug`: `promptly`]
:::

The `Promptly` provider includes processors that are high level abstractions built on top of processors/models from other providers. For example, it includes processors like `Text-Chat` built on top of other LLM chat models and natively implements a RAG pipeline.

## Text-Chat

:::info[`processor_slug`: `text_chat`]
:::

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

:::info[`processor_slug`: `datasource_search`]
:::

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

:::info[`processor_slug`: `http_api_processor`]
:::

The `HTTP API` processor allows you to make HTTP requests to any API. It supports GET, POST, PUT, DELETE methods and closely follows the OpenAPI specification. It also supports authentication using API keys, OAuth2, etc. You can also use the `HTTP API` processor to make requests to the LLMStack or Promptly APIs.

### Input

- `input_data`; Input for parameter keys as JSON.

### Configuration

- `url`: The URL to make the HTTP request to.
- `path`: Path to append to the URL. You can add a prameter by encolosing it in single brackets `{param}` and the value for the parameter will be taken from the `input_data` input.
- `method`: HTTP method to use for the request.
- `content_type`: Content type of the request.
- `parameters`: List of acceptable parameters for the request.
  - `name`: Name of the parameter.
  - `location`: Location of the parameter. Can be `query`, `header`, `path`, `cookie`.
  - `required`: Whether the parameter is required or not.
  - `description`: Description of the parameter. This will be used when generating the OpenAPI specification and when using the processor as a tool in Agents.
  - `value`: Default value for the parameter.
- `request_body`: Body for the request
  - `parameters`: List of acceptable parameters for the request body. JSON body will be generated from these parameters as keys.
    - `name`: Name of the parameter.
    - `type`: Type of the parameter. Can be `string`, `number`, `integer`, `boolean`, `array`.
    - `required`: Whether the parameter is required or not.
    - `description`: Description of the parameter. This will be used when generating the OpenAPI specification and when using the processor as a tool in Agents.
  - `payload`: Optional payload to use for the request body. Body is usually generated from the `parameters` keys and values. If `payload` is provided, it will be used as the body for the request instead. In the payload, you can use `{{<param_name>}` to access body params or `{{_connection.<key>}}` to access connection configurations. Make sure to provide valid JSON in the payload when the `content_type` is `application/json`.
  - `connection_id`: Connection ID to use for the request. Create connections from the `Settings` page and use them here if you want to access an authenticated API.
  - `allow_redirects`: Whether to allow redirects or not.
  - `timeout`: Timeout for the request in seconds.

### Output

- `code`: Status code of the response.
- `headers`: A dictionary of headers of the response.
- `text`: Text of the response.
- `content_json`: JSON content of the response.
- `is_ok`: Whether the response is OK or not.
- `url`: URL of the response.
- `encoding`: Encoding of the response.
- `cookies`: A dictionary of cookies in the response.
- `elapsed`: Time elapsed for the request in seconds.

## Web Search

:::info[`processor_slug`: `web_search`]
:::

The `Web Search` processor allows you to search the web using a search engine like Google and iterate through results and their source urls.

:::note
If you are using LLMStack, make sure you have configured the `default_google_custom_search_api_key` and `default_google_custom_search_cx` in the `.llmstack/config` file.
:::

### Input

- `query`: The query to search in the web.

### Configuration

- `search_engine`: Search engine to use for the search. Only `Google` is supported for now.
- `k`: Maximum number of results to retrieve from the search engine.

### Output

- `results`: Array of results from the search engine.
  - `text`: Text of the result.
  - `source`: Source of the result.

## Static Web Browser

:::info[`processor_slug`: `static_web_browser`]
:::

The `Static Web Browser` allows you to interact with a web page, perform a given set of instructions like clicking on a button, filling a form, etc., and extract data from the web page at the end of the instructions. It can optionally use connections to authenticate with the web page so you can interact with authenticated pages like your linkedin profile, internal company documentation, etc.

### Input

- `url`: The URL of the web page to interact with.
- `instructions`: The instructions to perform on the web page. Each instruction is a dictionary with the following keys:
  - `type`: Type of the instruction. Can be `Click`, `Type`, `Wait`, `Goto`, `Copy`, `Enter`, `Scrollx`, `Scrolly` and `Terminate`.
  - `selector`: Selector to use for the instruction. This can be a CSS selector or an XPath selector.
  - `data`: Value to use for the instruction. This is used for `Type`, `Wait`, `Goto`, `Scollx` and `Scrolly` instructions where you need to provide a value. For example when used with `Scrollx` instruction, we provide the number of pixels to scroll by in `data`.

### Configuration

- `connection_id`: Connection ID of type `Web Login` to use for the web page. Create connections from the `Settings` page and use them here if you want to access an authenticated web page.
- `stream_video`: Whether to stream the video of the web page or not. This is useful when you want to see the web page in real time while the instructions are being performed.
- `timeout`: Timeout for the instructions in seconds.

### Output

- `text`: Text of the web page after performing the instructions.
- `video`: Video of the web page after performing the instructions. This is only available if `stream_video` is set to `true`. In order to render the video, you need to use `![video](data:videostream/output._video)` in the output template.
- `content`: A dictionary representing the content of the web page after performing the instructions. This is useful when you want to extract data from the web page
  - `url`: URL of the web page.
  - `title`: Title of the web page.
  - `text`: Text of the web page.
  - `screenshot`: Screenshot of the web page.
  - `error`: Error if any.
  - `buttons`: List of buttons on the web page.
    - `text`: Text of the button.
    - `selector`: Selector of the button.
  - `inputs`: List of inputs on the web page.
    - `text`: Text of the input.
    - `selector`: Selector of the input.
  - `selects`: List of selects on the web page.
    - `text`: Text of the select.
    - `selector`: Selector of the select.
  - `textareas`: List of textareas on the web page.
    - `text`: Text of the textarea.
    - `selector`: Selector of the textarea.
  - `links`: List of links on the web page.
    - `text`: Text of the link.
    - `selector`: Selector of the link.
    - `url`: URL of the link.

## Web Browser

:::info[`processor_slug`: `web_browser`]
:::

The `Web Browser` processor is similar to the `Static Web Browser` processor but instead of performing a fixed set of instructions, it will take a `task` and a `start_url` as input and autogenerate instructions to perform the task. This is useful as a general purpose web browser that can be used to perform any task on any web page in agent workflows.

### Input

- `start_url`: The URL of the web page to interact with.
- `task`: Details of the task to perform

### Configuration

- `connection_id`: Connection ID of type `Web Login` to use for the web page. Create connections from the `Settings` page and use them here if you want to access an authenticated web page.
- `model`: LLM model to use to inspect the web page and generate instructions.
- `stream_video`: Whether to stream the video of the web page or not. This is useful when you want to see the web page in real time while the instructions are being performed.
- `stream_text`: Whether to stream the thinking text or not.
- `timeout`: Timeout for the instructions in seconds.
- `max_steps`: Maximum number of steps to perform for the task.
- `system_message`: System message to use for the LLM. This processor comes with a default system message that works well for most tasks. You can override it with your own system message if you want to.
- `seed`: Seed to use with the model. This is useful when you want to get the same answer for the same question.

### Output

See the output of the [`Static Web Browser`](#output-4) processor.

## URL Extractor

:::info[`processor_slug`: `http_uri_text_extract`]
:::

Extracts text from a URL and optionally filter the content semantically based on a given `query`. If the url is for a video, it will extract the audio from the video and transcribe it.

### Input

- `url`: The URL to extract text from.
- `query`: An optional query to semantic search in the extracted text.

### Configuration

- `document_limit`: Maximum number of documents to retrieve from the vector store for the asked query.
- `text_chunk_size`: Chunk size of document to use for semantic search.

### Output

- `text`: The extracted text from the URL.

## File Extractor

:::info[`processor_slug`: `data_uri_text_extract`]
:::

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
