---
id: introduction
title: Connections
---

Often times, you will need to connect your app to external services to perform certain tasks. For example, you might want to send an email to your customer, or make an API call to a service, or connect to your database to fetch some data or login to an internal website to scrape some data etc. LLMStack/Promptly connections allows you to store your credentials for these external services in a secure way and use them in your apps.

![Connections](/img/ui/llmstack-settings.png)

To add a connection, click on the `+ Connection` button on the top right corner of the `Settings` page. You can add the following types of connections:

### Web Login

You can add a web login connection to login to a website and use with url data sources or in processors like `Web Browser`. To add a web login connection, click on the `+ Connection` button on the top right corner of the `Settings` page and select `Web Login` from the dropdown. Enter a name, description and start url for the connection and click on `Test Connection`. This will open a modal with a remote browser. Login to the website using the remote browser and click on `Done` button once you are logged in. This will save the cookies and other credentials in the connection and you can use this connection with url data sources or in processors like `Web Browser`.

:::info
You can login to multiple websites using the same `Web Login` connection if you want to perform multiple tasks in the same app.
:::

:::note
You cannot paste clipboard into the remote browser. You will need to type the credentials manually.
:::

![Web Login](/img/ui/web-login-connection.png)

### Google Login

You can add a google login connection to login to your google account and use with google drive data sources. To add a google login connection, use the `Google Login` type and click on `Login with Google`. Once the app is authorized to access your google account, you can use this connection with google drive data sources.

### API Key

You can add an API key connection to store your API keys.

### Bearer Token

You can add a bearer token connection to store your bearer tokens.

### Basic Auth

You can add a basic auth connection to store your basic auth credentials.
