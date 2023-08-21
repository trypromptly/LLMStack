---
id: development
title: Development
---

To start LLMStack in development mode, clone the github repo and run the following commands to build client and server:

```bash
git clone https://github.com/trypromptly/LLMStack.git
cd LLMStack/client
npm install
npm run build
cd ..
docker compose -f docker-compose.dev.yml --env-file .env.dev up --build
```

The client will be available at [http://localhost:3000](http://localhost:3000) and the server will be available at [http://localhost:9000](http://localhost:9000).

Modify the environment variables in `.env.dev` to suit your needs. Refer to the [configuration](config.md) section for more information.
