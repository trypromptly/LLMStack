---
id: cohere
title: Cohere
---

The `Cohere` provider includes processors for models from [Cohere](https://cohere.com).

## Generate

### Input

- `prompt`: The prompt to ask the Cohere Generate model.
- `env`: Optional Cohere API input environment.

### Configuration

- `model`: The size of the model to generate with. Currently available models are medium and xlarge (default). Smaller models are faster, while larger models will perform better. Custom models can also be supplied with their full ID.
- `preset`: The ID of a custom playground preset. You can create presets in the playground. If you use a preset, the prompt parameter becomes optional, and any included parameters will override the preset's parameters.

### Output

- `choices`: A list of generated completions, with the most likely completion first.
- `metadata`: Additional information about the generation, such as the model used and the number of tokens generated.
