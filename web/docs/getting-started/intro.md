---
id: introduction
title: Getting Started
---

import ReactPlayer from "react-player";

:::info
Check out our Cloud offering at [Promptly](https://trypromptly.com) or follow the instructions below to deploy LLMStack on your own infrastructure.
:::

## Prerequisites

- [Python](https://www.python.org/downloads/) (version 3.8 or above)

## Installation

You can install LLMStack locally using the following command:

```
pip install llmstack
```

:::info
LLMStack comes with a default admin account whose credentials are `admin` and `promptly`. _Be sure to change the password from admin panel after logging in_.
:::

:::info
If you are on Windows, please use WSL2 (Windows Subsystem for Linux) to install LLMStack. You can follow the instructions [here](https://docs.microsoft.com/en-us/windows/wsl/install-win10) to install WSL2. Once you are in a WSL2 terminal, you can install LLMStack using the above command.
:::

Once installed, you can start LLMStack using the following command:

```
llmstack
```

LLMStack should automatically open your browser and point it to login page on [http://localhost:3000](http://localhost:3000). You can also alternatively open [http://localhost:3000](http://localhost:3000) to login into the platform.

LLMStack creates a config file in your home directory at `~/.llmstack/config` to store the configuration. You can change the port and other settings from this file. Refer to the [configuration](config.md) section for more information.

<ReactPlayer
  playing
  controls
  url="/img/llmstack-demo.m4v"
  width="100%"
  height="100%"
  loop
/>

:::note
If you are deploying LLMStack on a server, make sure to update `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` in `~/.llmstack/config` file to include the hostname of your server. Refer to the [configuration](config.md) section for more information.
:::

Instead of downloading the release, you can also clone the repository and run the above commands in the cloned repository.

```
git clone https://github.com/trypromptly/LLMStack.git
```

You can add your own keys to providers like OpenAI, Cohere, Stability etc., from Settings page. If you want to provide default keys for all the users of your LLMStack instance, you can add them to the `~/.llmstack/config` file.

## Updating

To update LLMStack to the new release, you can run the following command:

```
pip install llmstack --upgrade
```

## Key Concepts

### Processors

Processors are the basic building blocks in LLMStack. These provide the functionality to process the input from user or from a previous processor in a chain, take some action and optionally generate a response. LLMStack comes with a few built-in processors like OpenAI's ChatGPT, Image Generation, Stability's Image Generation etc. You can also create your own processors and add them to LLMStack.

### Providers

Providers are the entities that provide the functionality to the processors. For example, OpenAI's ChatGPT processor uses OpenAI's API to generate text. LLMStack comes with a few built-in providers like OpenAI, Cohere, Stability etc. Providers act as namespaces for the processors. You can also create your own providers and add them to LLMStack.

### Apps

Apps are the final product of LLMStack. Apps are created by chaining multiple processors together. LLMStack provides a visual editor to create apps. Apps can be shared with other users of LLMStack installation. Apps can be invoked using APIs, from the UI or triggered from Slack, Discord etc.

### Datasources

Datasources are used to provide context to LLMs to build applications that can perform tasks on your data. LLMStack allows you to import data from various sources like CSV, PDF, URLs, Youtube etc., and use them in your apps. When a datasource is created, LLMStack chunks the data based on the type, creates embeddings and saves them in a vector database included in the installation. Datasources can also be shared with other users of LLMStack installation in the context of an organization.

### Variables

Variables are used in LLMStack to provide dynamic values to the processors. For example, you can use variables to provide the name of the user to the processors. Variables are provided in the form `{{name}}` where `name` is the variable name. In App editor, data from previous processors/steps is available as variables and can be used in subsequent processors/steps.

:::tip
If you have questions, suggestions or need help, feel free to join our [Discord server](https://discord.gg/3JsEzSXspJ) or start a discussion on our [Github Discussions](https://github.com/trypromptly/LLMStack/discussions) page.
:::
