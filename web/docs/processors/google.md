---
id: google
title: Google
---

The `Google` provider includes processors for PaLM2 models from [Google's Vertex AI](https://cloud.google.com/vertex-ai).

## PaLM2 for Chat

### Input

- `messages`: List of text messages in the conversation history. Messages are in chronological order, with the oldest message first and the newest message last.
- `context`: Optional context for the conversation. This can be used to specify the topic of the conversation, the user's goals, or any other information that may be relevant to the model's response.
- `examples`: Optional list of conversation examples. This can be used to teach the model how to respond to different types of prompts and conversations.

### Configuration

`datasources`: List of datasource UUIDs to use to retrieve data from the vector store for the asked question. If not provided, it will not provide any context to the PaLM2 model.

- `temperature`: The temperature is used for sampling during the response generation, which occurs when topP and topK are applied. Temperature controls the degree of randomness in token selection. Lower temperatures are good for prompts that require a more deterministic and less open-ended or creative response, while higher temperatures can lead to more diverse or creative results. A temperature of 0 is deterministic: the highest probability response is always selected. For most use cases, try starting with a temperature of 0.2.
- `maxOutputTokens`: Optional maximum number of tokens that can be generated in the response. Specify a lower value for shorter responses and a higher value for longer responses.
- `topK`: Optional top-k changes how the model selects tokens for output. A top-k of 1 means the selected token is the most probable among all tokens in the model's vocabulary(also called greedy decoding), while a top-k of 3 means that the next token is selected from among the 3 most probable tokens(using temperature).
- `topP`: Optional top-p changes how the model selects tokens for output. Tokens are selected from most K(see topK parameter) probable to least until the sum of their probabilities equals the top-p value. For example, if tokens A, B, and C have a probability of 0.3, 0.2, and 0.1 and the top-p value is 0.5, then the model will select either A or B as the next token(using temperature) and doesn't consider C. The default top-p value is 0.95.
- `auth_token:` Optional Google API key.
- `project_id`: Optional Google project ID.

### Output

- `content`: The generated response content.
- `citationMetadata`: Optional metadata for the citations found in the response.
- `safetyAttributes`: Optional safety attributes for the response.

## PaLM2 for Text

PaLM2 for Text is a text processor that uses the PaLM2 language model to generate text. It can be used to generate different creative text formats, like poems, code, scripts, musical pieces, email, letters, etc.

### Input

The input to the PaLM2 for Text processor is a `prompt`. The prompt is a string that describes the text that you want to generate. For example, you could use the prompt "Write a poem about a cat." to generate a poem about a cat.

### Configuration

The configuration for the PaLM2 for Text processor includes the following parameters:

- `temperature`: The temperature controls the randomness of the generated text. A higher temperature will result in more creative and diverse text, but it may also be less accurate.
- `max_output_tokens`: The maximum number of tokens to generate.
- `top_k`: The top-k parameter controls the number of tokens that the model considers when generating the next token. A higher top-k value will result in more accurate text, but it may also be less creative.
- `top_p`: The top-p parameter controls the probability of the next token being selected. A higher top-p value will result in more predictable text, but it may also be less creative.
- `auth_token`: Your Google API key.
- `project_id`: Your Google project ID.

## Output

The output of the PaLM2 for Text processor is a `TextPrediction` object. The `TextPrediction` object contains the following fields:

- `content`: The generated text.
- `citationMetadata`: A list of citations for the text that was generated.
- `safetyAttributes`: A list of safety attributes for the text that was generated.
