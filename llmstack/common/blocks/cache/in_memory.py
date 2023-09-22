import hashlib

from llmstack.common.blocks.base.processor import CacheManager


def get_hash(input: dict):
    return hashlib.sha256(str(input).encode('utf-8')).hexdigest()


class InMemoryCache(CacheManager):
    def __init__(self):
        self.cache = {}

    def set(self, key, value):
        self.cache[key] = value

    def get(self, key):
        return self.cache.get(key)

    def delete(self, key):
        if key in self.cache:
            del self.cache[key]
