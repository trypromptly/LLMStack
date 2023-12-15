---
id: introduction
title: Getting Started
---

import ReactPlayer from "react-player";

:::info
Check out our Cloud offering at [Promptly](https://trypromptly.com) or follow the instructions below to deploy LLMStack on your own infrastructure. If you are using Promptly, you can skip this section and go to [Key Concepts](#key-concepts) section.
:::

## Prerequisites

- [Python](https://www.python.org/downloads/) (version 3.9 or above)
- [Docker](https://docs.docker.com/get-docker/) (if you want to use jobs or browser automation)

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

:::note
When you start LLMStack for the first time, it will download the required docker images. This may take a few minutes depending on your internet connection.
:::

<ReactPlayer
  playing
  controls
  url="/img/llmstack-demo.m4v"
  width="100%"
  height="100%"
  loop
/>

:::note
If you are deploying LLMStack on a server, make sure to update `allowed_hosts` and `csrf_trusted_origins` in `~/.llmstack/config` file to include the hostname of your server. Refer to the [configuration](config.md) section for more information.
:::

You can add your own keys to providers like OpenAI, Cohere, Stability etc., from Settings page. If you want to provide default keys for all the users of your LLMStack instance, you can add them to the `~/.llmstack/config` file.

## Upgrading

To upgrade LLMStack to the latest release, you can run the following command:

```
pip install llmstack --upgrade
```

## Key Concepts

### Processors

Processors are the basic building blocks in LLMStack. These provide the functionality to process the input from user or from a previous processor in a chain, take some action and optionally generate a response. LLMStack comes with a few built-in processors like OpenAI's ChatGPT, Image Generation, Stability's Image Generation etc. You can also create your own processors and add them to LLMStack.

#### Tools

Tools are processors that can be used to perform some action when used in the context of [agents](#agents). For example, you can use `ChatGPT` processor with a prompt to generate essays as a tool in an Agent app and the agent will use the tool whenever it needs to generate an essay.

### Providers

Providers are the entities that provide the functionality to the processors. For example, OpenAI's ChatGPT processor uses OpenAI's API to generate text. LLMStack comes with a few built-in providers like OpenAI, Cohere, Stability etc. Providers act as namespaces for the processors. You can also create your own providers and add them to LLMStack.

### Apps

Apps are the final product of LLMStack. Apps are created by chaining multiple processors together. LLMStack provides a visual editor to create apps. Apps can be shared with other users of LLMStack installation. Apps can be invoked using APIs, from the UI or triggered from Slack, Discord etc.

#### Agents

Agents are the autonomous apps that can perform tasks on your behalf. Agents use the provided processors as tools to perform tasks. For example, you can create an agent to act as an SDR (Sales Development Representative) and use it to send emails to your leads, using the processors provided by LLMStack as tools.

### Datasources

Datasources are used to provide context to LLMs to build applications that can perform tasks on your data. LLMStack allows you to import data from various sources like CSV, PDF, URLs, Youtube etc., and use them in your apps. You can even connect to external datastores and use them as datasources in LLMStack. When a datasource is created, LLMStack chunks the data based on the type, creates embeddings and saves them in a vector database included in the installation. Datasources can also be shared with other users of LLMStack installation in the context of an organization.

### Connections

Connections are used to store encrypted credentials for your external services like databases, APIs etc. Connections can be used in processors to connect to external services or in datasources to import data from external datastores.

### Variables

Variables are used in LLMStack to provide dynamic values to the processors. For example, you can use variables to provide the name of the user to the processors. Variables are provided in the form `{{name}}` where `name` is the variable name. In App editor, data from previous processors/steps is available as variables and can be used in subsequent processors/steps.

:::tip
If you have questions, suggestions or need help, feel free to join our [Discord server](https://discord.gg/3JsEzSXspJ) or start a discussion on our [Github Discussions](https://github.com/trypromptly/LLMStack/discussions) page.
:::
