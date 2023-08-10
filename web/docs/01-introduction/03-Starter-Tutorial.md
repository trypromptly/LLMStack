---
title: Starter Tutorial
sidebar_label: Starter Tutorial
---
## Create a Story Generator application

In this tutorial we will create a simple story generator application. The application will generate a story based on a theme provided by the user. The application will use ChatGPT to generate a story and Dall-E to generate an image for the story.

### Start LLMStack
Clone the repository
   ```bash
   git clone https://github.com/trypromptly/LLMStack.git
   ```
Compile the frontend code
```bash
cd LLMStack/client
npm run build
```

Build and start the docker image
   ```bash
   docker-compose -f docker-compose.dev.yml -d --build --env-file .env.dev up 
   ```
In you browser visit `http://localhost:9000` and login with the default admin account.

[TODO: Add screenshot of login page]

### Update API Keys
The application will use OpenAI's ChatGPT and OpenAI's Dall-E to generate the story and image respectively. Both these models require an API key to access the API. To update the API key, visit the settings page and add your OpenAI key.

[TODO: Add screenshot of settings page]

### Create a new application
To create a new application click on **Web App** under `Create a new App from scratch` section on the home page. This will open the application builder UI. 
[TODO: Add steps]

### Preview the application
Upon completing the above steps, hit save. Now you can preview your app by clicking the **Preview** item in the left hand side menu. This will render your web app in the existing browser tab. 
Now enter the theme for the story and click on the **Submit** button. ✨Voila!✨ You have generated your first story.

### Publish the application
You can continue iterating on your prompt to improve the story generation. Once you are happy with the results, you can publish the application by clicking on the **Publish** button. This will make the application available to others to use.