from openai import OpenAI
from openai._client import SyncAPIClient


class LLMClient(SyncAPIClient):
    pass


class LLM(LLMClient, OpenAI):
    pass
