from llama_index.core.base.embeddings.base import BaseEmbedding


class EmbeddingsGenerator(BaseEmbedding):
    provider_slug: str = "openai"
    embedding_model_name: str = "ada"

    @classmethod
    def class_name(cls) -> str:
        return "EmbeddingsGenerator"
