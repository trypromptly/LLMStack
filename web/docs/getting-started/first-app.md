---
id: first-app
title: Build your first App
---

import ReactPlayer from "react-player";

:::note
This guide assumes that you have already deployed LLMStack on your infrastructure. If you haven't, please follow the [Getting Started](/docs/getting-started/introduction) guide.
:::

Getting started with LLMStack is easy. In this guide, we will walk you through the process of building your first app, a story generator app using OpenAI's ChatGPT and Image generation models.

The goal of the app is to generate a story based on a theme provided by the user, and generate an image based on the generated story. We will use ChatGPT to generate the story and prompt to generate the image. We will then use OpenAI's image generation model to generate image from the prompt. Let's go!

<ReactPlayer
  playing
  controls
  url="/img/llmstack-storygenerator.m4v"
  width="100%"
  height="100%"
  loop
/>

1. Point your browser to your LLMStack installation and **Login into LLMStack** using your account credentials. Default installation uses `admin` as username and `promptly` as password.
2. Click on **Web App** tile under "Create a new App" section.
3. Enter the name of your app, e.g. `Story Generator` and click on **Create App** button.
4. You will be redirected to the app page with **Editor** tab open.
5. Modify the **Input** field to take the theme for the story. We will use `theme` as the name of the input field.
6. **Add ChatGPT processor** by clicking on the `+Processor` button. If the button is not green/clickable, make sure you select _OpenAI_ in the `Provider` dropdown and select _ChatGPT_ in the `Backend` dropdown.
7. **Configure ChatGPT processor** to generate a story for a given theme. Wire the theme variable from input as user's message.
8. **Add and configure second ChatGPT processor** by clicking on `+Processor` button to generate a prompt for image generation. Wire the output of the first ChatGPT processor as user's message to the second ChatGPT processor.
9. **Add and configure OpenAI image generation processor** by selecting `Image Generations` in Backend dropdown and clicking on `+Processor` button. Wire the output of the second ChatGPT processor as prompt to the image generation processor.
10. **Configure output** to display the generated story and image. Click on the `Application Output` block and add the variables corresponding to output of the first ChatGPT processor for story and output of the OpenAI image generation processor for image.
11. **Save the app** by clicking on the `Save` button on the top bottom corner of the editor.
12. **Preview the app** by selecting the `Preview` tab on the left and providing an example theme in the input field. You should see the generated story and image in the output section.
13. **Publish the app** by clicking on the `Publish` button on the top right corner of the app page.
14. Your app is now ready to be used by your users. You can share the app link with your users or embed the app in your website. You can also invoke the app **using the API or call it from Slack or Discord**.
