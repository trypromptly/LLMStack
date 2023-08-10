---
id: discord
title: Discord
sidebar_label: Discord
---

Each application built on LLMstack can be accessed using Discord. It is essential to follow the instructions given below to ensure that your interaction with the platform works without glitches.

## Prerequisites 

1. **Public Access:** Your LLMstack application needs to be publicly reachable. Discord operates across the internet, making it necessary for it to have a way to connect to your LLMStack installation. If your application is protected by a firewall or is on a private network, it is impossible for Discord to interact with it. Ensure therefore that your LLMstack platform is hosted so that it can receive incoming HTTP(S) requests from Discord.

2. **Discord Application:** A Discord app is essential to enable a user to invoke your app from Discord. This app on Discord will become the bridge that interconnects your Discord server and your LLMstack app. In case you have not created a Discord app as yet, you can easily do that by navigating to https://discord.com/developers/applications and clicking `New Application`. Make sure to give your Discord app sufficient BOT permissions to undertake necessary actions. This can be done in the `BOT` section of your Discord app settings.

3. **App Installation on Server:** The next prerequisite is to install your app into your Discord server. This might require admin permissions and you may need to check your role or consult with your server admin if necessary.

  To install an application in your workspace:

   - Access the `OAuth2` section on your app settings page on the Discord developer portal.
   - Tweak the `URL Generator` section to provide the necessary permissions and copy the generated URL.
   - Open this URL in a web browser, select your server, and click on `Authorize`.


## Process Flow

1. A user from your Discord server invokes your application by using the app’s command and providing the required application input. Say your app is named `MyTestApp`, the user can invoke it by typing `/MyTestApp Hello World` in a channel.

2. The user's command is then processed by Discord and it dispatches an HTTPS request to your LLMstack application. This request contains a payload incorporating the user's message, the channel it was transmitted from, amongst other related details.

3. Your LLMstack application accepts the request and uses the message provided by the user as application input and executes the pertinent actions. The output from the application is delivered as a reply to the user's message.

## Note:

Refer to the relevant Discord API documentation for a comprehensive understanding about Discord apps creation and management.