from functools import cache

from llmstack.data.sources.files.csv import CSVFileSchema
from llmstack.data.sources.files.file import FileSchema
from llmstack.data.sources.files.pdf import PdfSchema
from llmstack.data.sources.text.text_data import TextSchema
from llmstack.data.sources.website.url import URLSchema

__all__ = ["FileSchema", "TextSchema", "URLSchema"]


@cache
def get_source_cls(slug, provider_slug):
    for cls in [CSVFileSchema, FileSchema, PdfSchema, URLSchema, TextSchema]:
        if cls.slug() == slug and cls.provider_slug() == provider_slug:
            return cls

    return None
