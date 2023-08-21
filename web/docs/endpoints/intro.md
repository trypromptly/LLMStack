---
id: introduction
title: Endpoints
---

Endpoints are instances of processors with predefined configuration parameters and can optionally include variables to be filled during runtime. They are available as HTTP APIs that can be invoked using the API key and the endpoint UUID. Endpoints are useful for creating multiple versions of the same processor with different configuration parameters. They can be versioned and form building blocks for apps.

To illustrate how endpoints are used, imagine you have perfected a prompt for GPT-4 that allows you to extract structured information from a given text. You can create an endpoint with `ChatGPT` processor and the prompt as configuration on LLMStack. You can now use this endpoint in your application to extract structured information from text. If you need to make changes to the prompt, you can create a new version of the endpoint in LLMStack without changing the application code.

## Variables

Variables are placeholders in the input or configuration that can be filled during runtime. They are useful for creating dynamic endpoints that can be used for multiple purposes. For example, you can create an endpoint for summarizing text with a variable for the length of the summary. You can then use this endpoint for summarizing text with different lengths.

You can use variables in the input or configuration by using the following syntax:

```
{{variable_name}}
```

## Creating an endpoint

Endpoints are created from Playground ([http://localhost:3000/playground](http://localhost:3000/playground)) in LLMStack. Make sure `Create New` is selected in the toggle and select the processor you want to create an endpoint for. You can then fill in the input and configuration parameters and click on `Submit` to test configuration. Once it runs successfully, you can click on `Save Endpoint` and fill in the endpoint information to create an endpoint.

Once an endpoint is saved, it is available as an HTTP API that can be invoked using the API key and the endpoint UUID. You can get the endpoint UUID by clicking on the API tab in the endpoint output page.

## Versioning

Endpoints can be versioned to allow for multiple versions of the same endpoint. Versioning is useful for creating new versions of the same endpoint without changing the application code. For example, you can create a new version of an endpoint by updating prompt for GPT-4 without changing the application code.

To create a new version of an existing endpoint, select the endpoint you want to update from the Existing endpoint dropdown in LLMStack playground. You can then update the input and configuration parameters and click on `Submit` to test configuration. Once it runs successfully, you can click on `Save Version` and fill in the endpoint information to create a new version of the endpoint.

## API

Endpoints are available as HTTP APIs that can be invoked using the API key and the endpoint UUID. You can get the endpoint UUID by clicking on the API tab in the endpoint output page. For example,

:::info
You can get your LLMStack token from your profile settings page at [http://localhost:3000/settings](http://localhost:3000/settings).
:::

:::tip
If you have used any variables in the input or configuration, you can fill them in the template_values field in the request body. For example, if you have a variable `length` in the configuration, you can fill it in the request body as follows:

```json
{
  "template_values": {
    "length": 100
  }
}
```

:::

```bash
curl -X POST https://localhost:3000/api/endpoints/<UUID> \
    -H 'Content-Type: application/json' \
    -H 'Authorization: Token <LLMSTACK_TOKEN>' \
    -d '{"template_values": <KEY_VALUE_JSON>}'
```
