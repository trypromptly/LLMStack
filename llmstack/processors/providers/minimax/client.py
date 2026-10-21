from llmstack.processors.providers.minimax import MiniMaxProviderConfig


def create_minimax_client(provider_config: MiniMaxProviderConfig, http_client=None):
    from llmstack.common.utils.sslr import LLM

    base_url = provider_config.base_url.rstrip("/")
    client_options = {"http_client": http_client} if http_client is not None else {}

    if base_url.endswith("/anthropic"):
        return LLM(
            provider="anthropic",
            anthropic_api_key=provider_config.api_key,
            base_url=f"{base_url}/v1",
            **client_options,
        )

    return LLM(
        provider="openai",
        openai_api_key=provider_config.api_key,
        openai_base_url=base_url,
        **client_options,
    )
