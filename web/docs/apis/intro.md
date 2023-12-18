---
id: introduction
title: APIs
---

LLMStack provides a set of APIs that you can use to access the functionality of LLMStack. You can use these APIs to run apps, manage your data sources etc.,

## Authentication

All LLMStack APIs require authentication. You can authenticate using your API Token. You can find your API Token in your [LLMStack Settings](https://localhost:3000/settings). You can pass your API Token in the `Authorization` header with `Token` prefix.

## Streaming Output

For app runs, if `stream` parameter is used, output is received in chunks of values for JSON keys. For example, if the output is a JSON object with keys `a`, `b` and `c`, you will receive the output in the following format:

```json
{
  "a": <A_VALUE_CHUNK>,
  "b": <B_VALUE_CHUNK>,
  "c": <C_VALUE_CHUNK>
}
```

You will need to parse the output in your client code and stitch the chunks together to get the complete output.

## API Reference

### Apps

#### Run an app.

```bash
POST /api/apps/<app_uuid>/run
```

or

```bash
POST /api/apps/<app_uuid>/run/<session_id>
```

where `session_id` is a unique identifier for the session. You can use the same session id to run the app multiple times. If you don't pass a session id, LLMStack will generate a random session id for you.

##### Request body

You can pass the values for the app's input variables in the request body. You can also pass `stream` parameter to stream the response.

```json
{
  "input": <KEY_VALUE_JSON>,
  "stream": <BOOLEAN>
}
```

##### Response body

```json
{
  "session": {
    "id": <SESSION_ID>,
  },
  "output": <APP_OUTPUT>
}
```

#### Create an App

You can create an app by sending a POST request to `/api/apps` with the app definition as `YAML` in the request body. Make sure to set the `Content-Type` header to `application/yaml`.

```bash
POST /api/apps
```

#### Update an App

You can update an app by sending a PATCH request to `/api/apps/<app_uuid>` with the app definition as `YAML` in the request body. Make sure to set the `Content-Type` header to `application/yaml`.

```bash
PATCH /api/apps/<app_uuid>
```

### Datasources

#### List datasources

```bash
GET /api/datasources
```

##### Response body

```json
[
  {
    "uuid": <DATASOURCE_UUID>,
    "name": <DATASOURCE_NAME>,
    "type": <DATASOURCE_TYPE>,
    "created_at": <DATASOURCE_CREATED_AT>,
    "updated_at": <DATASOURCE_UPDATED_AT>,
  },
  ...
]
```

#### Create a datasource

```bash
POST /api/datasources
```

##### Request body

```json
{
  "name": <DATASOURCE_NAME>,
  "type": <DATASOURCE_TYPE>,
}
```

##### Response body

```json
{
  "uuid": <DATASOURCE_UUID>,
  "name": <DATASOURCE_NAME>,
  "type": <DATASOURCE_TYPE>,
  "created_at": <DATASOURCE_CREATED_AT>,
  "updated_at": <DATASOURCE_UPDATED_AT>,
}
```

#### Delete a datasource

```bash
DELETE /api/datasources/<datasource_uuid>
```

#### Add entry to a datasource

```bash
POST /api/datasources/<datasource_uuid>/entries
```

##### Request body

```json
{
  "entry_data": {
    "name": "<ENTRY_NAME>",
    "content": "<ENTRY_CONTENT>",
    "url": "<ENTRY_URL>",
    "file": "<BASE64_ENCODED_FILE_DATA>"
  },
  "entry_metadata": {
    "key1": "value1",
    "key2": "value2"
  }
}
```

`content`, `url` and `file` parameters are optional. You can pass any one of them based on the type of datasource. `entry_metadata` is an optional key-value JSON object that can be used to store additional metadata about the entry. It is used when you want to filter entries based on metadata during vector search.

:::note
Metadata keys will be available with `md_` prefix in the vector store. For example, if you have a metadata key `key1`, it will be available as `md_key1` in the vector store. There is default metadata like `source` available on all entries and is auto generated based on the entry.
:::

#### Delete entry from a datasource

```bash
DELETE /api/datasources/<datasource_uuid>/entries/<entry_uuid>
```

#### List entries in a datasource

```bash
GET /api/datasources/<datasource_uuid>/entries
```
