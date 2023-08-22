---
id: config
title: Configuration
---

You can configure the LLMStack installation by editing the `.env` file in the root directory of the installation. The `.env` file is a simple text file with key-value pairs. You can edit the file using any text editor. Following is the list of available configuration options:

| Key                    | Description                                                                                                                                                                                                | Default Value                                                       |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `SECRET_KEY`           | Secret key for your installation. This is the key used for signing data. **_Make sure this is changed_**                                                                                                   | Hardcoded random string.                                            |
| `CIPHER_KEY_SALT`      | Salt used to encrypt user keys and other sensitive data                                                                                                                                                    | `salt`                                                              |
| `DATABASE_PASSWORD`    | Password for the database user. This is used when setting up the initial db user and for connecting to the database later                                                                                  | `llmstack`                                                          |
| `POSTGRES_VOLUME`      | Path to the directory where the database data will be stored. By default, data is stored in `/tmp` which is ephemeral. Make sure to change this to a persistent directory if you want to persist the data. | `/tmp/postgres_llmstack`                                            |
| `REDIS_VOLUME`         | Path to the directory where the redis data will be stored. By default, data is stored in `/tmp` which is ephemeral. Make sure to change this to a persistent directory if you want to persist the data.    | `/tmp/redis_llmstack`                                               |
| `WEAVIATE_VOLUME`      | Path to the directory where the weaviate data will be stored. By default, data is stored in `/tmp` which is ephemeral. Make sure to change this to a persistent directory if you want to persist the data. | `/tmp/weaviate_llmstack`                                            |
| `LLMSTACK_PORT`        | Port on which the LLMStack web server will listen.                                                                                                                                                         | `3000`                                                              |
| `LOG_LEVEL`            | Log level for the LLMStack web server.                                                                                                                                                                     | `ERROR`                                                             |
| `ALLOWED_HOSTS`        | Comma separated list of allowed hosts for the LLMStack API server server. If you are running LLMStack on a non localhost domain, you need to add allowed hosts                                             | `localhost`                                                         |
| `CSRF_TRUSTED_ORIGINS` | Comma separated list of trusted origins. If you are running LLMStack on a non localhost domain, you need to add the domain to this list.                                                                   | `http://127.0.0.1:{LLMSTACK_PORT},http://localhost:{LLMSTACK_PORT}` |

## Default Platform Keys

You can set default keys for providers like OpenAI, Cohere etc., for all apps from the `.env` file. These keys will be used for all apps unless overridden by individual users from their settings page. To run LLMs locally, you can also run [LocalAI](https://localai.io/) setup and use it from LLMStack by configuring the LocalAI endpoint and the key. Following is the list of available keys for configuration:

| Key                                       | Description                                                                             | Default Value |
| ----------------------------------------- | --------------------------------------------------------------------------------------- | ------------- |
| `DEFAULT_OPENAI_API_KEY`                  | Default OpenAI API key ChatGPT, Image generation, whisper and other models from OpenAI. | None          |
| `DEFAULT_DREAMSTUDIO_API_KEY`             | Default DreamStudio API key to use for all apps for Stability models.                   | None          |
| `DEFAULT_AZURE_OPENAI_API_KEY`            | Default Azure OpenAI API key if the user wants to Azure's OpenAI.                       | None          |
| `DEFAULT_COHERE_API_KEY`                  | Default Cohere API key to use for all apps.                                             | None          |
| `DEFAULT_FOREFRONTAI_API_KEY`             | Default ForefrontAI API key to use for all apps.                                        | None          |
| `DEFAULT_ELEVENLABS_API_KEY`              | Default Eleven Labs API key for text to speech processor.                               | None          |
| `DEFAULT_LOCALAI_API_KEY`                 | Default LocalAI API to your installation .                                              | None          |
| `DEFAULT_LOCALAI_BASE_URL`                | Default LocalAI base URL of the installation.                                           | None          |
| `DEFAULT_AWS_SECRET_ACCESS_KEY`           | Default AWS Secret Access Key to use for all apps.                                      | None          |
| `DEFAULT_AWS_DEFAULT_REGION`              | Default AWS Default Region to use for all apps.                                         | None          |
| `DEFAULT_AWS_ACCESS_KEY_ID`               | Default AWS Access Key ID to use for all apps.                                          | None          |
| `DEFAULT_GOOGLE_SERVICE_ACCOUNT_JSON_KEY` | Default Google Service Account JSON Key for Google's Vertex AI offering.                | None          |
