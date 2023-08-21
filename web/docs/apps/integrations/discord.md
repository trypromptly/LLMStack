---
id: discord
title: Discord
---

You can call LLMStack Apps from Discord using the [Discord Slash Commands](https://discord.com/developers/docs/interactions/slash-commands) feature. Follow the steps below to set up a Discord Slash Command to call an LLMStack App.

![Discord Integration](/img/ui/discord.png)

## Create a Discord Application

To create a Discord bot, visit [https://discord.com/developers/applications](https://discord.com/developers/applications) and click the “New Application” button. You’ll be prompted to give your app a name. Once you’ve done that, you’ll be taken to the app configuration page. Fill other fields like description and app icon as needed.

## Install the Discord Bot

:::tip
Your LLMStack app needs to be publicly reachable for Discord to be able to call it. If you are running LLMStack locally, you can use a tool like [ngrok](https://ngrok.com/) to make your app publicly reachable. Or you can use [Promptly](https://trypromptly.com), which is a hosted version of LLMStack.
:::

To add the Discord Bot to the server you can generate a URL by visiting the URL Generator section under OAuth2. When generating an installation URL make sure that you select the bot scope to ensure that the Discord bot has the required permissions to respond to slash commands.

Make sure you select `Send Messages` & `Use Slash Commands` permission under **Bot Permissions** section.

Copy the generated URL, visit the URL in your browser and select the server you want to add the bot to. You’ll be prompted to authorize the bot to be installed in your server. Click `Authorize` to install the bot in your server. Once done, you’ll be taken back to the app configuration page where you can see the bot added to your server.

## Connect the Discord Bot to LLMStack App

Navigate to `Integrations -> Discord` in the LLMStack App and click on the `Add Discord Bot` button. You’ll be prompted to enter the Discord Bot Token. To get the token, navigate to the `Bot` section under the `Settings` menu in the Discord Developer Portal. Copy the token and paste it in the LLMStack App. Click `Save` to save the Discord Bot Token.
