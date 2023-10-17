---
id: elevenlabs
title: Eleven Labs
---

The `ElevenLabs` provider includes processors for text to speech models from [Eleven Labs](https://elevenlabs.io/).

## Text to Speech

### Input

- `input_text`: The text to convert to speech.

### Configuration

- `voice_id`: The voice ID to be used. You can find a list of all available voices at <https://api.elevenlabs.io/v1/voices>.
- `model_id`: The identifier of the model to be used. You can find a list of all available models at <https://api.elevenlabs.io/v1/models>.
- `optimize_streaming_latency`: Whether to optimize for streaming latency. This can reduce the quality of the generated audio.
- `voice_settings`: Voice settings.

### Output

- `audio_content`: The generated audio content in base64 format.
