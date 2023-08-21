---
id: slack
title: Slack
---

To call your LLMStack app from a Slack channel, you need to first create a Slack app in your Slack workspace and use that configuration in your app's `Integration -> Slack` configuration. Follow the steps below to set up a Slack app to call your LLMStack app.

![Slack Integration](/img/ui/slack.png)

## Create a Slack App

To create a Slack app, visit [https://api.slack.com/apps](https://api.slack.com/apps) and click the `Create New App` button. Pick `From scratch`, you’ll be prompted to give your app a name and select a workspace to install it in. Once you’ve done that, you’ll be taken to the app configuration page.

Click on `OAuth & Permissions` under `Features` section in the sidebar and add the following scopes under `Bot Token Scopes` section:

Once added, click on `Install to Workspace` button under `OAuth Tokens for the workspace` section. You’ll be prompted to authorize the app to be installed in your workspace. Click `Allow` to install the app in your workspace. Once done, you’ll be taken back to the app configuration page where you can see `Bot User OAuth Token`.

## Connect the Slack App to LLMStack App

:::tip
Your LLMStack app needs to be publicly reachable for Slack to be able to call it. If you are running LLMStack locally, you can use a tool like [ngrok](https://ngrok.com/) to make your app publicly reachable. Or you can use [Promptly](https://trypromptly.com), which is a hosted version of LLMStack.
:::

Go to `Integrations -> Slack` in the LLMStack App and fill in the information in the form from the Slack app configuration page. Click `Save` to save the LLMStack app configuration.

Now go to your Slack app’s configuration page and click on `Event Subscriptions` under `Features` section in the sidebar. Turn on `Enable Events` and paste the URL from the LLMStack app’s Slack configuration page. Click `Save Changes` to save the configuration.

After this, you’ll need to subscribe to the following bot events under `Subscribe to Bot Events` section:

`app_mention`

Click `Save Changes` to save the configuration. You’ll be prompted to reinstall the app in your workspace. Click `Reinstall App` to reinstall the app in your workspace. You should now be able to add the app to your Slack channels and call it from there which will trigger the LLM app and return the output.
