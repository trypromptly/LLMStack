---
id: introduction
title: Getting Started
---

import ReactPlayer from "react-player";

:::info
Check out our Cloud offering at [Promptly](https://trypromptly.com) or follow the instructions below to deploy LLMStack on your own infrastructure.
:::

## Prerequisites

- [Docker](https://docs.docker.com/engine/install/)
- [Git](https://git-scm.com/downloads) (optional)

## Quickstart

Download the latest release from LLMStack's [releases page](https://github.com/trypromptly/LLMStack/releases) and extract it. Navigate to the extracted directory and create your `.env` file and update `SECRET_KEY`, `CIPHER_SALT` and `DATABASE_PASSWORD`:

```
cp .env.prod .env
```

Run LLMStack using the following command:

```
./run-llmstack.sh
```

> If you are on Windows, you can use `run-llmstack.bat` instead

Once LLMStack is up and ready, it should automatically open your browser and point it to login page on [http://localhost:3000](http://localhost:3000). You can also alternatively use `docker compose up --pull always` to manually start the containers and open [http://localhost:3000](http://localhost:3000) to login into the platform. Make sure to wait for the API server to be ready before trying to load LLMStack.

:::info
LLMStack comes with a default admin account whose credentials are `admin` and `promptly`. _Be sure to change the password from admin panel after logging in_.
:::

<ReactPlayer
  playing
  controls
  url="/img/llmstack-demo.m4v"
  width="100%"
  height="100%"
  loop
/>

Instead of downloading the release, you can also clone the repository and run the above commands in the cloned repository.

```
git clone https://github.com/trypromptly/LLMStack.git
```

Users of the platform can add their own keys to providers like OpenAI, Cohere, Stability etc., from Settings page. If you want to provide default keys for all the users of your LLMStack instance, you can add them to the `.env` file. Make sure to restart the containers after adding the keys.

:::caution
Remember to update `POSTGRES_VOLUME`, `REDIS_VOLUME` and `WEAVIATE_VOLUME` in `.env` file if you want to persist data across container restarts.
:::

## Key Concepts

### Processors

Processors are the basic building blocks in LLMStack. These provide the functionality to process the input from user or from a previous processor in a chain, take some action and optionally generate a response. LLMStack comes with a few built-in processors like OpenAI's ChatGPT, Image Generation, Stability's Image Generation etc. You can also create your own processors and add them to LLMStack.

### Providers

Providers are the entities that provide the functionality to the processors. For example, OpenAI's ChatGPT processor uses OpenAI's API to generate text. LLMStack comes with a few built-in providers like OpenAI, Cohere, Stability etc. Providers act as namespaces for the processors. You can also create your own providers and add them to LLMStack.

### Endpoints

Endpoints are instances of processors. You can create multiple endpoints based on a single processor. For example, you can create multiple endpoints for OpenAI's ChatGPT processor with different parameters and prompts. These endpoints can be invoked using APIs. Endpoints also form the basis of apps in LLMStack. When an app is created by chaining multiple processors, LLMStack creates an endpoint each of those processors and connects them together.

### Apps

Apps are the final product of LLMStack. Apps are created by chaining multiple processors together. LLMStack provides a visual editor to create apps. Apps can be shared with other users of LLMStack installation. Apps can be invoked using APIs, from the UI or triggered from Slack, Discord etc.

### Datasources

Datasources are used to provide context to LLMs to build applications that can perform tasks on your data. LLMStack allows you to import data from various sources like CSV, PDF, URLs, Youtube etc., and use them in your apps. When a datasource is created, LLMStack chunks the data based on the type, creates embeddings and saves them in a vector database included in the installation. Datasources can also be shared with other users of LLMStack installation in the context of an organization.

### Variables

Variables are used in LLMStack to provide dynamic values to the processors. For example, you can use variables to provide the name of the user to the processors. Variables are provided in the form `{{name}}` where `name` is the variable name. In App editor, data from previous processors/steps is available as variables and can be used in subsequent processors/steps.
