---
id: introduction
title: Processors
---

A processor is the smallest building block in LLMStack. It is a function that takes some input, does something with it, and returns some output. Each processor defines its own input, configuration, and output schemas. You can quickly test processors in the Processor Playground at [http://localhost:3000/playground](http://localhost:3000/playground).

## Providers

Processors are grouped into providers. They act as namespaces for processors. For example, the `OpenAI` provider hosts all processors that interact with the models provided by `Open AI` like `ChatGPT`, `Text completions`, `image generation`, etc.

Let's take a look at the providers and their processors that are available in the default installation of LLMStack.

| Provider                                  | Processors                                                                                                                                       |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| [Anthropic](/docs/processors/anthropic)   | Completions                                                                                                                                      |
| [Azure](/docs/processors/azure)           | ChatGPT                                                                                                                                          |
| [Cohere](/docs/processors/cohere)         | Generate                                                                                                                                         |
| [ElevenLabs](/docs/processors/elevenlabs) | Text to Speech                                                                                                                                   |
| [Google](/docs/processors/google)         | Gemini, Text to Speech                                                                                                                           |
| [HeyGen](/docs/processors/heygen)         | Realtime Avatar                                                                                                                                  |
| [LinkedIn](/docs/processors/linkedin)     | Profile Extractor                                                                                                                                |
| [LocalAI](/docs/processors/localai)       | Audio Transcription, Audio Translation, ChatGPT, ChatGPT with Vision, Completions, Image generation, Image variation, Image edit, Text to Speech |
| [OpenAI](/docs/processors/openai)         | Audio Transcription, Audio Translation, ChatGPT, ChatGPT with Vision, Completions, Image generation, Image variation, Image edit, Text to Speech |
| [Promptly](/docs/processors/promptly)     | File Extractor, Datasource Search, HTTP API, URL Extractor, Web Browser, Static Web Browser, Text-Chat, Web Search                               |
| [Stability](/docs/processors/stability)   | Image2Image, Text2Image                                                                                                                          |
