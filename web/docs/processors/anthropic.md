---
id: anthropic
title: Anthropic
---

The `Anthropic` provider includes models from [Anthropic](https://www.anthropic.com/).

## Completions

Text completions model from Anthropic, Claude.

### Input

- `prompt`: The prompt to ask the Anthropic Completions model.

### Configuration

- `model`: The Anthropic Completions model to use. `claude-2` and `claude-instant` are currently supported.
- `max_tokens_to_sample`: The maximum number of tokens allowed for the generated answer.
- `temperature`: The sampling temperature to use for generating responses.

### Output

- `completion`: The model generated response.
