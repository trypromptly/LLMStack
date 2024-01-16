import importlib
import json
import logging
from enum import Enum
from typing import Any, Dict, Generic, List, Optional

from pydantic import Field

from llmstack.common.blocks.base.processor import (BaseConfiguration,
                                                   BaseConfigurationType,
                                                   BaseInput, BaseInputType,
                                                   BaseOutput, BaseOutputType,
                                                   CacheManager,
                                                   ProcessorInterface, Schema)
from llmstack.common.utils.utils import retrier

logger = logging.getLogger(__name__)


class OpenAIEmbeddingInput(BaseInput):
    text: str


class OpenAIEmbeddingOutputMetadata(Schema):
    raw_response: Dict[str, Any]


class OpenAIEmbeddingOutput(BaseOutput):
    metadata: OpenAIEmbeddingOutputMetadata
    embeddings: List[float]


class EmbeddingAPIProvider(str, Enum):
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"

    def __str__(self):
        return self.value


class OpenAIEmbeddingConfiguration(BaseConfiguration):
    max_retry_attemps: int = Field(default=3)
    max_retry_wait: int = Field(default=20)
    min_retry_wait: int = Field(default=1)
    timeout: int = Field(default=60)
    api_type: EmbeddingAPIProvider
    model: Optional[str] = None
    endpoint: Optional[str] = None
    deploymentId: Optional[str] = None
    apiVersion: Optional[str] = None
    api_key: str = None


class OpenAIEmbeddingsProcessor(
    ProcessorInterface[
        OpenAIEmbeddingInput,
        OpenAIEmbeddingOutput,
        OpenAIEmbeddingConfiguration,
    ],
    Generic[
        BaseInputType,
        BaseOutputType,
        BaseConfigurationType,
    ],
):
    def __init__(
        self,
        configuration: dict,
        cache_manager: CacheManager = None,
        input_tx_cb: callable = None,
        output_tx_cb: callable = None,
    ):
        super().__init__(configuration, cache_manager, input_tx_cb, output_tx_cb)

    def process(
        self,
        input: OpenAIEmbeddingInput,
        configuration: OpenAIEmbeddingConfiguration,
    ) -> OpenAIEmbeddingOutput:
        import openai

        importlib.reload(openai)

        result = None
        metadata = {}
        num_tries = configuration.max_retry_attemps + 1
        timeout = configuration.timeout
        min_retry_wait = configuration.min_retry_wait
        max_retry_wait = configuration.max_retry_wait

        @retrier(
            exceptions=[],
            num_tries=num_tries,
            min_delay=min_retry_wait,
            max_delay=max_retry_wait,
            backoff=2,
        )
        def _get_openai_embedding(text: str, api_key: str, model: str):
            openai.api_type = "open_ai"
            openai.api_key = api_key
            return openai.Embedding.create(
                input=[text],
                model=model,
                timeout=timeout,
            )

        @retrier(
            exceptions=[],
            num_tries=num_tries,
            min_delay=min_retry_wait,
            max_delay=max_retry_wait,
            backoff=2,
        )
        def _get_azure_openai_embedding(
            text: str,
            api_key: str,
            api_version: str,
            endpoint: str,
            deployment_id: str,
        ):
            openai.api_version = api_version
            openai.api_base = f"https://{endpoint}.openai.azure.com"
            openai.api_type = "azure"
            openai.api_key = api_key
            return openai.Embedding.create(
                input=[text],
                deployment_id=deployment_id,
                timeout=timeout,
            )

        if configuration.api_type == EmbeddingAPIProvider.AZURE_OPENAI:
            result = _get_azure_openai_embedding(
                text=input.text,
                api_key=configuration.api_key,
                api_version=configuration.apiVersion,
                endpoint=configuration.endpoint,
                deployment_id=configuration.deploymentId,
            )
        else:
            result = _get_openai_embedding(
                text=input.text,
                api_key=configuration.api_key,
                model=configuration.model,
            )
        try:
            embeddings = result["data"][0]["embedding"]
        except BaseException:
            raise Exception(
                f"Error while retrieving OpenAI Embedding: {result}",
            )

        for key in result:
            if key != "data":
                metadata[key] = json.loads(json.dumps(result[key]))

        return OpenAIEmbeddingOutput(
            embeddings=embeddings,
            metadata=OpenAIEmbeddingOutputMetadata(
                raw_response=metadata,
            ),
        )
