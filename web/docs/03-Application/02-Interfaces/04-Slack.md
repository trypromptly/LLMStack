---
id: slack
title: Slack
sidebar_label: Slack
---

Every application published on the LLMStack can be accessed via Slack, allowing you to invoke your workflows directly through the popular collaboration tool. Please ensure you adhere to the following prerequisites for successful operation.

## Prerequisites 

1. **Public Access:** Your LLMstack application must be publicly accessible. Since Slack operates over the internet, it must have a way to reach your LLMStack installation. If your application is behind a firewall or on a private network, there's no feasible means for Slack to interact with it. Ensure your LLMstack installation is hosted in such a way that it can receive incoming HTTP(S) requests from Slack.

2. **Slack Application:** To enable a user to invoke your application from Slack you need to create a Slack app. The Slack app will be the bridge between your Slack workspace and your LLMstack application. If you don't already have a Slack app, you can create one by navigating to https://api.slack.com/apps and clicking `Create New App`. Make sure to provide your Slack app with `app_mentions:read`, `chat:write`, `users:read` and `users:read.email` OAuth permissions. This can be done by visiting the `OAuth & Permissions` page of your Slack app settings dashboard.

3. **App Installation on Workspace:** The next prerequisite is to install your app into your Slack workspace. This will require administrative permissions, so check your role or consult with your workspace admin if necessary.

   To install an app into your workspace:
   - Access your app’s Basic Information page on the Slack app settings dashboard.
   - Find the Install your app to your workspace section, and click the `Install App to Workspace` button.
   - On the permissions page, review the requested scopes, and click `Allow`.

[TODO: Add screenshot of Slack app permissions page]

## Process Flow

1. A user in your Slack workspace invokes your application by mentioning the app name and providing the required application input. For example, if your app is named `MyTestApp` a user can invoke it by typing `@MyTestApp Hello World` in a channel or direct message.

2. When a user mentions your app with a message, Slack sends an HTTP request to your LLMstack application. The request contains a payload that includes the user's message, the channel it was sent from, and other relevant information.

3. Your LLMstack application receives the request, uses the user provided message as the input for the application, performs the necessary actions. The application then sends the output as a reply to the user's message.

## Note:

Please refer to the relevant Slack API documentation to understand more about creating and managing Slack apps.