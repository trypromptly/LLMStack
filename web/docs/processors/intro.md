---
id: introduction
title: Processors
---

A processor is the smallest building block in LLMStack. It is a function that takes some input, does something with it, and returns some output. Each processor defines its own input, configuration, and output schemas. You can quickly test processors in the Processor Playground at [http://localhost:3000/playground](http://localhost:3000/playground).

## Providers

Processors are grouped into providers. They act as namespaces for processors. For example, the `OpenAI` provider hosts all processors that interact with the models provided by `Open AI` like `ChatGPT`, `Text completions`, `image generation`, etc.

Let's take a look at the providers and their processors that are available in the default installation of LLMStack.
