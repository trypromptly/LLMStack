---
id: rag-with-realtime-avatar
title: Retrieval Augmented Generation with Realtime Avatar
description: Use HeyGen's Realtime Avatars and LLMStack / Promptly's retrieval augmented generation (RAG) to generate videos with your avatar repeating the answer in realtime.
---

import ReactPlayer from 'react-player';

import heygenConnectionImage from '@site/static/img/heygen-connection.png';
import realtimeAvatarChatAppNameImage from '@site/static/img/realtime-avatar-chat-app-name.png';
import realtimeAvatarChatTemplatePage1Image from '@site/static/img/realtime-avatar-chat-template-page1.png';
import realtimeAvatarChatTemplatePage2Image from '@site/static/img/realtime-avatar-chat-template-page2.png';

If you have been following the progress in the Generative video field, you'd have come across [HeyGen](https://www.heygen.com/) as the leader in AI generated avatar videos. Their [Realtime Avatars](https://www.heygen.com/article/unleashing-the-power-of-realtime-avatars) is a game changer in the field of video generation. With its Realtime Repeat API, we can make the avatar repeat any text in realtime. Combining this with LLMs opens up a lot of possibilities.

In this guide, we will see how to make your HeyGen avatar answer questions in realtime from your documents. We will use the [retrieval augmented generation (RAG)](/blog/retrieval-augmented-generation) pipeline to generate answers to questions and then use the answer to generate a video with the avatar repeating the answer in realtime.

Here is a demo of the app we will build in this guide:

<ReactPlayer
style={{ margin: "auto", paddingBottom: "20px" }}
playing
url="https://youtu.be/y8CAheAJC6o"
width={"850px"}
height={"500px"}
config={{
        youtube: {
          playerVars: {
            showinfo: 0,
            autoplay: 1,
            controls: 1,
          },
        },
      }}
/>

:::note
To make it easy to build your own avatar chatbot, we now include a `Realtime Avatar Chat` app template which this guide is based on
:::

### Prerequisites

:::info
Use the [cloud version of LLMStack at Promptly](https://trypromptly.com) to follow this guide without having to install LLMStack locally.
:::

- [LLMStack](/docs/getting-started/installation) installed and running
- [HeyGen](https://heygen.com) account with [API access](https://docs.heygen.com/docs/quick-start)

### Get your HeyGen API Key

To get your HeyGen API key, login to your HeyGen account and go to [API page](https://app.heygen.com/settings?nav=API). Make sure your HeyGen account plan has API access. While you are in your HeyGen account, create your instant avatar or pick one that you want to use. Make sure you get the avatar id and voice id for the avatar you want to use.

### Create HeyGen Connection in LLMStack / Promptly

Once you have your HeyGen API key, navigate to LLMStack / Promptly [settings page](https://trypromptly.com/settings) and create a new HeyGen connection by clicking on the `+ Connection` button. Pick a name for your connection and use `API Key Authentication` as the connection type. Enter your HeyGen API key in the `API Key` field, add <b>X-Api-Key\*</b> for the `Header Key` field and click on `Save`.

<img src={heygenConnectionImage} alt="HeyGen Connection" style={{ maxWidth: "600px", margin: "0 auto", display: "flex", paddingTop: "20px" }} />

## Create LLMStack / Promptly App

Once you have your key added as a connection, follow these steps to create an app on LLMStack / Promptly using the `Realtime Avatar Chat` template.

#### Step 1:

Navigate to the templates section on [apps page](https://trypromptly.com/apps) and find the `Realtime Avatar Chat` template. Click on the template card and create a new app using the template. Pick a name for your app and click on `Create App`.

<img src={realtimeAvatarChatAppNameImage} alt="Realtime Avatar Chat App Name" style={{ maxWidth: "600px", margin: "0 auto", display: "flex", paddingTop: "20px" }} />

#### Step 2:

Once the app is created, you will be taken to the template page. Fill the avatar id and voice id for the avatar you want to use. You can find the avatar id and voice id in your HeyGen account. Pick the connection you created with your HeyGen API key and click on `Next`.

<img src={realtimeAvatarChatTemplatePage1Image} alt="Realtime Avatar Chat Template Page 1" style={{ maxWidth: "600px", margin: "0 auto", display: "flex", paddingTop: "20px" }} />

:::tip
You can find the [voice ids](https://docs.heygen.com/reference/list-voices-v2) and [avatar ids](https://docs.heygen.com/reference/list-avatars-v2) in your account using the APIs listed in the [HeyGen API docs](https://docs.heygen.com/docs/quick-start).
:::

#### Step 3:

In the next step, you will be asked to pick a datasource for your app. You can pick your existing datasources or create a new datasource, add documents to that datasource by clicking on the `+` button. When asked a question, the app will search for the answer in the documents in the datasource you pick here, use GPT to generate an answer and make your avatar speak the answer in realtime. Once you have picked a datasource, click on `Save App`.

<img src={realtimeAvatarChatTemplatePage2Image} alt="Realtime Avatar Chat Template Page 2" style={{ maxWidth: "600px", margin: "0 auto", display: "flex", paddingTop: "20px" }} />

#### Step 4:

Once the app is saved, you can preview the app by clicking on the `Preview` option in the sidebar. You can also share the app with your friends and colleagues by publishing the app and sharing the published link. You can optionally invite your friends and colleagues to collaborate on the app by adding them in the publish settings.

You can input a question in the input box and click on the `Submit` button to see the avatar answer your question in realtime.

:::tip
To avoid hitting the API limits from HeyGen, you can close the session once you are done with the app. Hover over the video and click on the `Close Session` button.
:::
