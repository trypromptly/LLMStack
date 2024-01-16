import concurrent.futures
import importlib
import logging
import uuid
from enum import Enum
from typing import List, Optional

from asgiref.sync import async_to_sync
from django import db
from openai import AzureOpenAI, OpenAI
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.datasources.models import DataSource
from llmstack.datasources.types import DataSourceTypeFactory
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


class TextChatCompletionsModel(str, Enum):
    GPT_4 = "gpt-4"
    GPT_4_LATEST = "gpt-4-turbo-latest"
    GPT_3_5 = "gpt-3.5-turbo"
    GPT_3_5_LATEST = "gpt-3.5-turbo-latest"
    GPT_32_K = "gpt-4-32k"
    GPT_3_5_16K = "gpt-3.5-turbo-16k"

    def __str__(self):
        return self.value


class TextChatConfiguration(ApiProcessorSchema):
    model: TextChatCompletionsModel = Field(
        default=TextChatCompletionsModel.GPT_3_5,
        description="ID of the model to use. Currently, only `gpt-3.5-turbo` and `gpt-4` are supported.",
        widget="customselect",
        advanced_parameter=True,
    )
    datasource: List[str] = Field(
        default=None,
        description="Datasources to use",
        widget="datasource",
        advanced_parameter=False,
    )
    system_message_prefix: str = Field(
        """You are a helpful chat assistant""",
        description="System message that defines the character of the assistant",
        widget="textarea",
        advanced_parameter=True,
    )
    instructions: str = Field(
        """You are a chatbot that uses the provided context to answer the user's question.
If you cannot answer the question based on the provided context, say you don't know the answer.
No answer should go out of the provided input. If the provided input is empty, return saying you don't know the answer.
Keep the answers terse.""",
        description="Instructions for the chatbot",
        widget="textarea",
        advanced_parameter=True,
    )
    show_citations: bool = Field(
        title="Show citations",
        default=False,
        description="Show citations for the answer",
        advanced_parameter=True,
    )
    citation_instructions: str = Field(
        """Use source value to provide citations for the answer. Citations must be in a new line after the answer.""",
        widget="textarea",
        advanced_parameter=True,
        description="Instructions for the chatbot",
    )

    k: int = Field(
        title="Documents Count",
        default=5,
        description="Number of documents from similarity search to use as context",
    )
    chat_history_limit: int = Field(
        title="Chat history limit",
        default=20,
        description="Number of chat history to keep in memory",
    )
    temperature: float = Field(
        title="Temperature",
        default=0.7,
        description="Temperature of the model. Higher temperature results in more random completions. Try 0.9 for more fun results.",
    )
    use_azure_if_available: bool = Field(
        title="Use Azure if available",
        default=True,
        description="Use Azure if available. Will fallback to OpenAI when unchecked",
        advanced_parameter=True,
    )
    use_localai_if_available: bool = Field(
        title="Use LocalAI if available",
        default=False,
        description="Use LocalAI if available. Will fallback to OpenAI or Azure OpenAI when unchecked",
        advanced_parameter=True,
    )
    chat_history_in_doc_search: int = Field(
        title="Chat history in doc search",
        default=0,
        description="Number of messages from chat history to include in doc search",
        advanced_parameter=True,
    )
    hybrid_semantic_search_ratio: Optional[float] = Field(
        default=0.75,
        description="Ratio of semantic search to hybrid search",
        ge=0.0,
        le=1.0,
        multiple_of=0.01,
        advanced_parameter=True,
    )
    seed: Optional[int] = Field(
        description="Seed for the model",
        advanced_parameter=True,
    )


class TextChatInput(ApiProcessorSchema):
    question: str = Field(..., description="Question to answer")
    search_filters: str = Field(
        title="Search filters",
        default=None,
        description="Search filters on datasource entry metadata. You can provide search filters like `source == url1 || source == url2`. Click on your data entries to get your metadata",
        advanced_parameter=True,
    )


class Citation(ApiProcessorSchema):
    text: str
    source: Optional[str]
    certainty: Optional[float]
    distance: Optional[float]


class TextChatOutput(ApiProcessorSchema):
    answer: str = Field(
        ...,
        description="Answer to the question",
        widget="textarea",
    )
    citations: Optional[List[Citation]]


class TextChat(
    ApiProcessorInterface[TextChatInput, TextChatOutput, TextChatConfiguration],
):
    """
    Text summarizer API processor
    """

    def process_session_data(self, session_data):
        self._chat_history = session_data["chat_history"] if "chat_history" in session_data else []
        self._context = session_data["context"] if "context" in session_data else ""

    @staticmethod
    def name() -> str:
        return "Text-Chat"

    @staticmethod
    def slug() -> str:
        return "text_chat"

    @staticmethod
    def description() -> str:
        return "Conversation style question and answering from provided data"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    @classmethod
    def get_output_template(cls) -> Optional[OutputTemplate]:
        return OutputTemplate(
            markdown="""{{answer}}
{% if citations %}

Citations:
{% for citation in citations %}

{{citation.text}}
{{citation.source}}
{% endfor %}
{% endif %}""",
        )

    def session_data_to_persist(self) -> dict:
        return {
            "chat_history": self._chat_history[-self._config.chat_history_limit :]
            if self._config.chat_history_limit > 0
            else [],
            "context": self._context,
        }

    def _search_datasources(self, input):
        docs = []

        def fetch_datasource_docs(datasource_uuid):
            output_docs = []
            try:
                datasource = DataSource.objects.get(
                    uuid=uuid.UUID(datasource_uuid),
                )
                datasource_entry_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
                    datasource.type,
                )
                datasource_entry_handler = datasource_entry_handler_cls(
                    datasource,
                )

                search_query = input["question"]
                search_filters = input["search_filters"]
                if (
                    len(
                        self._chat_history,
                    )
                    > 0
                    and self._config.chat_history_in_doc_search > 0
                ):
                    search_query = (
                        search_query
                        + "\n\n"
                        + "\n\n".join(
                            [m["content"] for m in self._chat_history[-self._config.chat_history_in_doc_search :]],
                        )
                    )

                output_docs = datasource_entry_handler.search(
                    alpha=self._config.hybrid_semantic_search_ratio,
                    query=search_query,
                    limit=self._config.k,
                    search_filters=search_filters,
                )
            except Exception as e:
                logger.error(
                    f"Error fetching docs from datasource {datasource_uuid}: {e}",
                )
            finally:
                db.connections.close_all()
                return output_docs

        if self._config.datasource and len(self._config.datasource) > 0:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(fetch_datasource_docs, datasource_uuid)
                    for datasource_uuid in self._config.datasource
                ]

                for future_result in concurrent.futures.as_completed(futures):
                    try:
                        docs.extend(future_result.result())
                    except Exception as e:
                        logger.error(f"Error fetching datasource docs: {e}")
                        pass

        return docs

    def process(self) -> dict:
        input = self._input.dict()
        output_stream = self._output_stream
        docs = self._search_datasources(input)

        if docs and len(docs) > 0:
            if "score" in docs[0].metadata:
                docs = sorted(
                    docs,
                    key=lambda d: d.metadata["score"],
                    reverse=True,
                )[: self._config.k]
            else:
                docs = docs[: self._config.k]

        if len(docs) > 0:
            self._context = ""
            for d in docs:
                self._context = self._context + "\n-----"
                self._context = self._context + "\nContent: " + d.page_content
                if self._config.show_citations:
                    self._context = (
                        self._context + "\nMetadata: " + ", ".join(f"{k}: {v}" for k, v in d.metadata.items())
                    )
            # Remove invalid characters from docs
            self._context = self._context.replace("\u0000", "")

        instructions = self._config.instructions
        if self._config.show_citations:
            instructions = instructions + " " + self._config.citation_instructions
        system_message = {
            "role": "system",
            "content": self._config.system_message_prefix,
        }

        context_message = {
            "role": "user",
            "content": instructions + "\n----\ncontext: " + self._context,
        }
        self._chat_history.append(
            {"role": "user", "content": input["question"]},
        )

        model = self._config.dict().get("model", "gpt-3.5-turbo")
        if model == "gpt-3.5-turbo-latest":
            model = "gpt-3.5-turbo-1106"
        elif model == "gpt-4-turbo-latest":
            model = "gpt-4-1106-preview"

        if self._env["azure_openai_api_key"] and self._config.use_azure_if_available:
            if model == "gpt-3.5-turbo":
                model = "gpt-35-turbo"
            elif model == "gpt-3.5-turbo-16k":
                model = "gpt-35-turbo-16k"
            elif model == "gpt-3.5-turbo-latest":
                model = "gpt-35-turbo-1106"

            openai_client = AzureOpenAI(
                api_key=self._env["azure_openai_api_key"],
                api_version="2023-03-15-preview",
                azure_endpoint=f'https://{self._env["azure_openai_endpoint"]}.openai.azure.com',
            )

            result = openai_client.chat.completions.create(
                model=model,
                messages=[system_message] + [context_message] + self._chat_history,
                temperature=self._config.temperature,
                stream=True,
                seed=self._config.seed,
            )
        elif self._env["localai_base_url"] and self._config.use_localai_if_available:
            openai_client = (
                OpenAI(
                    api_key=self._env["localai_api_key"],
                    base_url=self._env["localai_base_url"],
                )
                if self._env["localai_api_key"]
                else OpenAI(
                    base_url=self._env["localai_base_url"],
                )
            )

            result = openai_client.chat.completions.create(
                model=model,
                messages=[system_message] + [context_message] + self._chat_history,
                temperature=self._config.temperature,
                stream=True,
                seed=self._config.seed,
            )
        elif self._env["openai_api_key"] is not None:
            openai_client = OpenAI(
                api_key=self._env["openai_api_key"],
            )

            result = openai_client.chat.completions.create(
                model=model,
                messages=[system_message] + [context_message] + self._chat_history,
                temperature=self._config.temperature,
                stream=True,
                seed=self._config.seed,
            )
        else:
            raise Exception("No OpenAI API key provided")

        for data in result:
            if (
                data.object == "chat.completion.chunk"
                and len(
                    data.choices,
                )
                > 0
                and data.choices[0].delta
                and data.choices[0].delta.content
            ):
                async_to_sync(output_stream.write)(
                    TextChatOutput(
                        answer=data.choices[0].delta.content,
                    ),
                )

        if len(docs) > 0:
            async_to_sync(
                output_stream.write,
            )(
                TextChatOutput(
                    answer="",
                    citations=list(
                        map(
                            lambda d: Citation(
                                text=d.page_content,
                                source=d.metadata["source"],
                                distance=d.metadata["distance"] if "distance" in d.metadata else 0.0,
                            ),
                            docs,
                        ),
                    ),
                ),
            )

        output = output_stream.finalize()

        self._chat_history.append(
            {
                "role": "assistant",
                "content": output["answer"]
                if isinstance(
                    output,
                    dict,
                )
                else output.answer,
            },
        )

        return output
