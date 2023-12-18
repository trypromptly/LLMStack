---
id: yaml
title: YAML
---

LLMStack / Promptly apps can be defined using [YAML](https://yaml.org/) instead of the UI. This is useful when you want to version control your apps or create apps programmatically.

:::tip
You can see the YAML definition of an app by clicking on the `UI / YAML` toggle button on the bottom left of the app editor.
:::

## Structure

Following is an example YAML definition of an app:

```yaml
name: Website Chatbot
type_slug: text-chat
description: "Chatbot that answers questions from website visitors"
config:
  welcome_message: Hello
  assistant_image: null
input_fields:
  - description: Enter your question here
    name: question
    title: Question
    type: string
output_template:
  markdown: |
    {{_inputs1.answer}}
processors:
  - id: _inputs1
    name: Text-Chat
    description: Conversation style question and answering from provided data
    provider_slug: promptly
    processor_slug: text_chat
    config:
      model: gpt-3.5-turbo
      datasource:
        - 98146759-d853-4d9d-8f17-3c7f891ebf81
      system_message_prefix: You are a helpful chat assistant
      instructions: >-
        You are a chatbot that uses the provided context to answer the user's
        question.

        If you cannot answer the question based on the provided context, say you
        don't know the answer.

        No answer should go out of the provided input. If the provided input is
        empty, return saying you don't know the answer.

        Keep the answers terse.
      show_citations: false
      citation_instructions: >-
        Use source value to provide citations for the answer. Citations must be
        in a new line after the answer.
      k: 8
      chat_history_limit: 20
      temperature: 0.7
      use_azure_if_available: true
      use_localai_if_available: false
      chat_history_in_doc_search: 0
      hybrid_semantic_search_ratio: 0.75
      seed: null
    input:
      question: "{{_inputs0.question}} "
    output_template: {}
```

The YAML definition of an app has the following structure:

- `name`: The name of the app.
- `type_slug`: The slug of the app type.
- `description`: The description of the app.
- `config`: The configuration of the app.
- `input_fields`: The input fields of the app.
- `output_template`: The output template of the app.
- `processors`: The processors of the app.

## App Types

The following app types are supported:

- `text-chat`: Text chat app.
- `web`: Web app.
- `agent`: Agent app.

## App Configuration

The following configuration options are supported:

- `welcome_message`: The welcome message to display to the user.
- `assistant_image`: The image to display for the assistant.
- `suggested_messages`: The suggested messages to display to the user.

## Input Fields

The following input field types are supported:

- `string`: String input field.
- `number`: Number input field.
- `boolean`: Boolean input field.
- `text`: Text input field.
- `file`: File input field.
- `voice`: Voice input field.
- `select`: Select input field.
  :::note
  For `select` input field, values must be provided as `label:value` pairs separated by commas.
  :::

## Output Template

The following output template types are supported:

- `markdown`: Markdown output template.

## Processors

Processor definitions are defined as a list of processor objects. Each processor object has the following structure:

- `id`: The ID of the processor.
- `name`: The name of the processor.
- `description`: The description of the processor.
- `provider_slug`: The slug of the processor provider.
  :::info
  Refer to the [Processors](/docs/processors/introduction) section for a list of supported processors, their slugs, and their providers.
  :::
- `processor_slug`: The slug of the processor.
- `config`: The configuration of the processor.
- `input`: The input of the processor.
- `output_template`: The output template of the processor. This is needed when the processor is used as a tool in an agent.
