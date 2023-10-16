---
id: localai
title: LocalAI
---

You can run [LocalAI](https://localai.io) locally and use LLMStack to build AI apps on top of open source locally running LLMs.

:::note
Make sure you configured LocalAI base url and API key in LLMStack's `Settings`. Read more about using LocalAI in our [blog post](https://github.com/trypromptly/LLMStack/blob/main/web/blog/2023-08-17-run-os-llms-with-localai.md).
:::

`LocalAI` provides drop in replacement for `OpenAI` APIs. Refer to [OpenAI](/docs/processors/openai) for processor details and [LocalAI](https://localai.io), for the list of supported LLMs.

## LocalAI for text

### Input

- `prompt`: The text prompt to complete.

### Configuration

The configuration for the LocalAI text completions API Processor is a `CompletionsConfiguration` object. This object has the following fields:

- `base_url`: The base URL of the LocalAI API.
- `model`: The name of the LocalAI model to use.
- `max_tokens`: The maximum number of tokens allowed for the generated completion.
- `temperature`: The sampling temperature to use.
- `top_p`: An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.
- `timeout`: Timeout in seconds.
- `stream`: Whether to stream the output.

### Output

The output of the LocalAI text completions API Processor is a `CompletionsOutput` object. This object has the following field:

- `choices`: A list of strings, which are the model's generated completions.

## LocalAI for Chat

### Input

The input to the LocalAI Chat Completions API Processor is a `ChatCompletionInput` object. This object has the following fields:

- `system_message`: An optional message from the system, which will be prepended to the chat history.
- `messages`: A list of ChatMessage objects, each with a role and message text.
- `functions`: An optional list of FunctionCall objects, which the model may generate JSON inputs for.

### Configuration

The configuration for the LocalAI Chat Completions API Processor is a `ChatCompletionsConfiguration` object. This object has the following fields:

- `base_url`: The base URL of the LocalAI API.
- `model`: The name of the LocalAI model to use.
- `max_tokens`: The maximum number of tokens allowed for the generated answer.
- `temperature`: The sampling temperature to use.
- `stream`: Whether to stream the output.
- `function_call`: Controls how the model responds to function calls.

### Output

The output of the LocalAI Chat Completions API Processor is a `ChatCompletionsOutput` object. This object has the following fields:

- `choices`: A list of ChatMessage objects, which are the model's generated responses.
- `_api_response`: The raw API response.

## LocalAI Image Generation

### Input

- `prompt`: A text description of the desired image(s). The maximum length is 1000 characters.

### Configuration

- `base_url`: The base URL of the LocalAI API.
- `size`: The size of the generated images. Must be one of 256x256, 512x512, or 1024x1024.
- `timeout`: The timeout in seconds for the API request.

### Output

- `data`: A list of base64-encoded JSON strings, each representing a generated image.
