---
id: stability
title: Stability
---

The `Stability` provider includes processors for models from [Stability AI](https://stability.ai) hosted on [DreamStudio](https://dreamstudio.ai/).

## Text2Image

The `Text2Image` processor generates images from text prompts.

### Input

- `prompt`: A list of prompts to describe the image to generate.

### Configuration

- `engine_id`: The Stability AI Text2Image model to use.
- `height`: The height of the generated image in pixels.
- `width`: The width of the generated image in pixels.
- `cfg_scale`: A parameter that controls how closely the engine attempts to match a generation to the provided prompt.
- `sampler`: The sampling engine to use.
- `steps`: The number of diffusion steps performed on the requested generation.
- `seed`: A seed for random latent noise generation.
- `num_samples`: The number of images to generate.
- `guidance_preset`: A guidance preset to use for image generation.

### Output

- `answer`: A list of generated images as base64 encoded strings.

## Image2Image

### Input

- `init_image`: The initial image to generate from. This can be any image, such as a photo, drawing, or painting.
- `prompt`: The prompt to describe the desired changes to the image. The prompt can be as simple as a few words or as complex as a paragraph of text.

### Configuration

- `engine`: The Stability AI Image2Image model to use. There are a number of different models available, each with its own strengths and weaknesses.
- `height`: The height of the generated image in pixels.
- `width`: The width of the generated image in pixels.
- `cfg_scale`: Dictates how closely the engine attempts to match a generation to the provided prompt. v2-x models respond well to lower CFG (4-8), where as v1-x models respond well to a higher range (IE: 7-14).
- `sampler`: Sampling engine to use. If no sampler is declared, an appropriate default sampler for the declared inference engine will be applied automatically.
- `steps`: Affects the number of diffusion steps performed on the requested generation.
- `seed`: Seed for random latent noise generation. Deterministic if not being used in concert with CLIP Guidance. If not specified, or set to 0, then a random value will be used.
- `num_samples`: Number of images to generate. Allows for batch image generations.
- `guidance_preset`: CLIP guidance preset, use with ancestral sampler for best results.
- `guidance_strength`: How strictly the diffusion process adheres to the prompt text (higher values keep your image closer to your prompt).

### Output

- `images`: An array of generated images as base64 encoded strings.
