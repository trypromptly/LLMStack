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
pip install poetry
poetry install
poetry shell
llmstack
```

The client will be available at [http://localhost:3000](http://localhost:3000) and the server will be available at [http://localhost:9000](http://localhost:9000).

> You can skip running `npm install` and `npm run build` if you have already built the client before

For frontend development, you can use `REACT_APP_SERVER=http://localhost:3000 npm start` to start the development server in client directory. You can also use `npm run build` to build the frontend and serve it from the backend server.
