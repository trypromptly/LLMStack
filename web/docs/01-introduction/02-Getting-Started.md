---
sidebar_position: 2
title: Getting Started
sidebar_label: Getting Started
---

## Getting Started
To get started with LLMStack, you can either use the prebuilt release archive or build from source.

### Use Prebuilt Release
Download the latest release from [here](https://github.com/trypromptly/LLMStack/releases). Extract the archive and run the following command from the extracted directory.
```bash
cp .env.prod .env
```
:::info
If you would like to add any default keys to your LLMStack installation you can add by modifying the `.env` file. 
:::

Start the docker containers:
```bash
docker compose up
```

### Build from Source
1. Clone the repository
   ```bash
    git clone https://github.com/trypromptly/LLMStack.git
   ```
2. Compile the frontend code
   ```bash
    cd LLMStack/client
    npm run build
   ```
:::info
If running this command for the first make sure to install the dependencies by running `npm install` first.
:::
1. Build and start the docker image
   ```bash
   docker-compose -f docker-compose.dev.yml -d --build --env-file .env.dev up
   ```
2. Point your browser to `localhost:9000` to login into the platform. LLMStack deployment comes with a default **admin** account whose credentials are `admin` and `promptly`. Be sure to change the password from [admin panel](http://localhost:9000/admin/) after logging in.
