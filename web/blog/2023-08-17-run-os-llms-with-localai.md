---
title: Open Source LLMs with LocalAI
description: Build AI Apps with Open Source LLMs like Llama2 using LocalAI and LLMStack.
slug: /run-os-llms-on-llmstack-with-localai
authors: [ajhai, vegito22]
tags: [llmstack, localai, llama2, open-source]
hide_table_of_contents: false
---

Now build AI Apps using Open Source LLMs like Llama2 on LLMStack using [LocalAI](https://localai.io)

<!--truncate-->

LLMStack now includes [LocalAI](https://github.com/go-skynet/LocalAI/) support which means you can now run Open Source LLMs like Llama2, stable diffusion etc., locally and build apps on top of them using LLMStack.

![LocalAI](/img/ui/localai-example.png)

## What is LocalAI?

LocalAI is a drop-in replacement REST API that’s compatible with OpenAI API specifications for local inferencing. Read more about LocalAI [here](https://localai.io/).

## How to use LocalAI with LLMStack?

To use LocalAI with LLMStack, you need to have LocalAI running on your machine. You can follow the deployment instructions [here](https://localai.io/) to install LocalAI on your machine. Once LocalAI is up and running, you can configure LLMStack to use LocalAI by going to `Settings` and filling in the `LocalAI Base URL` and `LocalAI API Key` if any. Once done, click `Update` to save the configuration.

![LocalAI Configuration](/img/ui/localai-settings.png)

Once LocalAI is configured, you can use it in your apps by selecting `LocalAI` as the provider for processor and selecting the processor and model you want to use.

Are there any other open source LLM frameworks that you would like to see on LLMStack? Let us know in our github discussions [here](https://github.com/trypromptly/LLMStack/discussions).
