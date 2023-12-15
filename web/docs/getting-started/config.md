---
id: config
title: Configuration
---

You can configure the LLMStack installation by editing the `.llmstack/config` file in the user's home directory. The `config` file is in TOML format. You can edit the file using any text editor. Following is the list of available configuration options:

| Key                            | Description                                                                                                                                                    | Default Value                                                       |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `secret_key`                   | Secret key for your installation. This is the key used for signing data. **_Make sure this is changed_**                                                       | Hardcoded random string.                                            |
| `cipher_key_salt`              | Salt used to encrypt user keys and other sensitive data                                                                                                        | `salt`                                                              |
| `database_engine`              | Database engine to use for the LLMStack installation.                                                                                                          | `sqlite3`                                                           |
| `database_name`                | Name of the database to use for the LLMStack installation.                                                                                                     | `./llmstack.sqlite`                                                 |
| `database_password`            | Password for the database user. This is used when setting up the initial db user and for connecting to the database later                                      |                                                                     |
| `llmstack_port`                | Port on which the LLMStack web server will listen.                                                                                                             | `3000`                                                              |
| `log_level`                    | Log level for the LLMStack web server.                                                                                                                         | `ERROR`                                                             |
| `allowed_hosts`                | Comma separated list of allowed hosts for the LLMStack API server server. If you are running LLMStack on a non localhost domain, you need to add allowed hosts | `localhost`                                                         |
| `site_url`                     | URL of the LLMStack installation. This is used for generating links in emails and other places.                                                                | `http://localhost:{LLMSTACK_PORT}`                                  |
| `csrf_trusted_origins`         | Comma separated list of trusted origins. If you are running LLMStack on a non localhost domain, you need to add the domain to this list.                       | `http://127.0.0.1:{LLMSTACK_PORT},http://localhost:{LLMSTACK_PORT}` |
| `default_vector_database`      | Default vector database to use for all apps.                                                                                                                   | `chroma`                                                            |
| `default_vector_database_path` | Default path for the vector database. This is used for storing the vector database.                                                                            | `~/.llmstack/chromadb`                                              |

## Default Platform Keys

You can set default keys for providers like OpenAI, Cohere etc., for all apps from the `.env` file. These keys will be used for all apps unless overridden by individual users from their settings page. To run LLMs locally, you can also run [LocalAI](https://localai.io/) setup and use it from LLMStack by configuring the LocalAI endpoint and the key. Following is the list of available keys for configuration:

| Key                                       | Description                                                                             | Default Value |
| ----------------------------------------- | --------------------------------------------------------------------------------------- | ------------- |
| `default_openai_api_key`                  | Default OpenAI API key ChatGPT, Image generation, whisper and other models from OpenAI. | None          |
| `default_dreamstudio_api_key`             | Default DreamStudio API key to use for all apps for Stability models.                   | None          |
| `default_azure_openai_api_key`            | Default Azure OpenAI API key if the user wants to Azure's OpenAI.                       | None          |
| `default_cohere_api_key`                  | Default Cohere API key to use for all apps.                                             | None          |
| `default_forefront_api_key`               | Default ForefrontAI API key to use for all apps.                                        | None          |
| `default_elevenlabs_api_key`              | Default Eleven Labs API key for text to speech processor.                               | None          |
| `default_anthropic_api_key`               | Default Anthropic API key for models like Claude.                                       | None          |
| `default_localai_api_key`                 | Default LocalAI API to your installation .                                              | None          |
| `default_localai_base_url`                | Default LocalAI base URL of the installation.                                           | None          |
| `default_aws_secret_access_key`           | Default AWS Secret Access Key to use for all apps.                                      | None          |
| `default_aws_region`                      | Default AWS Default Region to use for all apps.                                         | None          |
| `default_aws_access_key_id`               | Default AWS Access Key ID to use for all apps.                                          | None          |
| `default_google_service_account_json_key` | Default Google Service Account JSON Key for Google's Vertex AI offering.                | None          |
| `default_google_custom_search_api_key`    | Default Google Custom Search API Key for Google's Custom Search API.                    | None          |
| `default_google_custom_search_cx`         | Default Google Custom Search CX for Google's Custom Search API.                         | None          |
