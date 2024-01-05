---
id: introduction
title: Datasources
---

Most LLM models are trained on public datasets. These datasets are large and contain a lot of information but they might not be relevant to your use case. For example, if you are building a chatbot for your store, you might want the chatbot to respond to questions about your inventory, your return policy, etc. By combining the capabilities of Language Models with your custom data, you can create powerful and personalized AI applications.

LLMStack allows you to seamlessly integrate your custom data with the pre-trained language models. You can simply upload your files, add urls or connect your external data sources and start using them as data sources in your LLM apps. LLMStack does the heavy lifting for you by chunking, tokenizing and indexing your data into the included vectorstore. You can then use the vectorstore to augment your language models and build powerful AI applications.

![Datasources](/img/ui/llmstack-datasources.png)

## Supported Data Sources

LLMStack supports the following data sources:

### Local Files

You can upload your files to LLMStack and use them as data sources. LLMStack supports the following file formats:

- Text files
- PDF files
- CSV files
- DOCX, PPTX, XLSX files
- Markdown files
- Media files (audio, video) - extract text from media files using speech to text APIs

### URLs

You can add URLs to LLMStack and use them as data sources. LLMStack will download the content from the URL and use it as a data source. You can add sitemap URLs to LLMStack and it will crawl the sitemap and download the content from the URLs in the sitemap.

#### Authenticated URLs

If you want to add urls that require authentication, like an internal documentation page etc., add a `Web Login` connection to your account from `Settings` page and login to the website you want to add urls for using the remote web browser. Once the connection is added, you can add urls from the website as a data source by selecting the associated connection.

### External Data Sources

You can connect your external data sources to LLMStack and use them as data sources. LLMStack supports the following external data sources:

#### Google Drive

:::note
In LLMStack, you should have a google project with Google Drive API enabled to use this feature.
:::

To load files from your google drive, add a `Google Login` connection from `Settings` page. Once the connection is added, you can add your google drive files as a data source.

#### Weaviate

You can connect your [Weaviate](https://weaviate.io) instance to LLMStack and use it as a data source.

#### SingleStore

LLMStack can connect to your [SingleStore](https://www.singlestore.com/) instance and allow you to query your database and use the results as a data source in your LLM apps.
