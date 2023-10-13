---
id: openai
title: OpenAI
---

The `OpenAI` provider includes processors that correspond to [models from OpenAI:](https://platform.openai.com/docs/models/overview).

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

## Completions

### Input

- `prompt`: The prompt to ask the OpenAI Completions model.
- `search_filters`: The search filters to use to retrieve data from a vector store as a string. It is of the format `key1 == value1 || key2 == value2` or `key1 == value1 && key2 == value2`.

### Configuration

`datasources`: List of datasource UUIDs to use to retrieve data from the vector store for the asked question. If not provided, it will not provide any context to the OpenAI Completions model.

- `model`: OpenAI Completions model to use.
- `temperature`: Temperature to use for the OpenAI Completions model.
- `max_tokens`: Maximum number of tokens to generate.

### Output

- `text`: The generated text from the OpenAI Completions model.

## Image generation

### Input

- `prompt`: The prompt to describe the image to generate.

### Configuration

- `model`: OpenAI Image generation model to use.
- `size`: The size of the generated image in pixels.
- `n`: The number of images to generate.

### Output

- `images`: An array of generated images as base64 encoded strings.

## Image variation

### Input

- `image`: The base64 encoded image to generate variations of.
- `n`: The number of variations to generate.

### Configuration

- `model`: OpenAI Image variation model to use.

### Output

- `images`: An array of generated image variations as base64 encoded strings.

## Image edit

### Input

- `image`: The base64 encoded image to edit.
- `mask`: The base64 encoded mask image to use for editing.
- `prompt`: The prompt to describe the edit to make.

### Configuration

- `model`: OpenAI Image edit model to use.

### Output

- `image`: The edited image as a base64 encoded string.

## Audio transcription

### Input

- `audio_file`: The audio file to transcribe.

### Configuration

- `model`: OpenAI Audio transcription model to use.

### Output

- `transcript`: The transcribed audio as a string.

## Audio translation

### Input

- `audio_file`: The audio file to translate.
- `source_language`: The source language of the audio.
- `target_language`: The target language of the translation.

### Configuration

- `model`: OpenAI Audio translation model to use.

### Output

- `transcript`: The translated audio as a string.
