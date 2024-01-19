---
id: heygen
title: HeyGen
---

The `HeyGen` provider includes processors that can use your HeyGen API key and perform various actions like generating avatars in real-time and make them answer questions from your datasources.

## Realtime Avatar

### Input

- `task_type`: The type of task to perform. Can be `repeat`, `talk`, `create_session`, `start_session`, `close_session` and `submit_ice_candidate`. Types other than `repeat` are used internally by the processor and not for direct use.
- `text`: The text to repeat.
- `session_id`: The session ID to use. If not provided, a session_id from app session will be used if available.

### Configuration

- `avatar_name`: Avatar ID to use for the session. You can find this in your HeyGen account or use the API to get a list of available avatars. See their [API documentation](https://docs.heygen.com/reference/list-avatars-v2) for more details.
- `voice_id`: Voice ID to use for the session. You can find this in your HeyGen account or use the API to get a list of available voices. See their [API documentation](https://docs.heygen.com/reference/list-voices-v2) for more details.
- `connection_id`: The connection ID of the HeyGen account to use. Add a connection of type `API Key Authentication` from Settings > Connections (and add your HeyGen API key).
- `reuse_session`: Whether to reuse the session or create a new one. If set to `true`, the session will be reused for subsequent requests. If set to `false`, a new session will be created for each `create_session` request.
- `quality`: The quality of the generated video stream. Can be `low`, `medium` or `high`. Defaults to `medium`.
- `input_stream`: When set to `true`, the input text will be streamed to the avatar. This is useful when you want to generate a video of the avatar speaking a long text. Defaults to `false`. This will make the avatar start speaking as soon as a sentence is available.

### Output

- `task_type`: The type of task performed.
- `task_response_json`: The response from the HeyGen API.
