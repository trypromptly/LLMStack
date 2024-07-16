from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.common.utils.splitter import CSVTextSplitter, SpacyTextSplitter
from llmstack.common.utils.text_extract import extract_text_elements


def extract_documents(
    file_data,
    content_key,
    mime_type,
    file_name,
    metadata,
    chunk_size=1500,
):
    docs = []
    elements = extract_text_elements(
        mime_type=mime_type,
        data=file_data,
        file_name=file_name,
    )
    file_content = "\n\n".join([str(el) for el in elements])

    if mime_type == "text/csv":
        docs = [
            Document(
                page_content_key=content_key,
                page_content=t,
                metadata=metadata,
            )
            for t in CSVTextSplitter(
                chunk_size=chunk_size,
                length_function=CSVTextSplitter.num_tokens_from_string_using_tiktoken,
            ).split_text(file_content)
        ]
    else:
        docs = [
            Document(
                page_content_key=content_key,
                page_content=t,
                metadata=metadata,
            )
            for t in SpacyTextSplitter(
                chunk_size=chunk_size,
            ).split_text(file_content)
        ]
    return docs


def get_source_cls(slug, provider_slug):
    from llmstack.data.sources.files.csv import CSVFileSchema
    from llmstack.data.sources.files.file import FileSchema
    from llmstack.data.sources.files.pdf import PdfSchema
    from llmstack.data.sources.text.text_data import TextSchema
    from llmstack.data.sources.website.url import URLSchema

    for cls in [CSVFileSchema, FileSchema, PdfSchema, URLSchema, TextSchema]:
        if cls.slug() == slug and cls.provider_slug() == provider_slug:
            return cls

    return None


def get_destination_cls(slug, provider_slug):
    from llmstack.data.destinations.vector_stores.legacy_chromadb import (
        PromptlyLegacyChromaDBVectorStoreConfiguration,
    )
    from llmstack.data.destinations.vector_stores.legacy_weaviate import (
        PromptlyLegacyWeaviateVectorStoreConfiguration,
    )

    for cls in [PromptlyLegacyWeaviateVectorStoreConfiguration, PromptlyLegacyChromaDBVectorStoreConfiguration]:
        if cls.slug() == slug and cls.provider_slug() == provider_slug:
            return cls

    return None
