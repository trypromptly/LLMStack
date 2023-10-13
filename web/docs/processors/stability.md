---
id: stability
title: Stability
---

The `Stability` provider includes processors for models from [Stability AI](https://stability.ai) hosted on [DreamStudio:](https://dreamstudio.ai/).

## Text2Image

### Input

- `prompt`: The prompt to describe the image to generate.

### Configuration

- `model`: Stability AI Text2Image model to use.
- `size`: The size of the generated image in pixels.
- `n`: The number of images to generate.

### Output

- `images`: An array of generated images as base64 encoded strings.
