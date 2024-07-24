def get_transformer_cls(slug, provider_slug):
    from llmstack.data.transformations.llamindex.splitters import SentenceSplitter

    for cls in [SentenceSplitter]:
        if cls.slug() == slug and cls.provider_slug() == provider_slug:
            return cls

    return None
