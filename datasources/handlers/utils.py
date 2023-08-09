from common.promptly.vectorstore import Document
from common.utils.splitter import CSVTextSplitter
from common.utils.text_extract import extract_text_elements
from common.utils.splitter import SpacyTextSplitter


def extract_documents(file_data, content_key, mime_type, file_name, metadata, chunk_size=1500):
    docs = []
    elements = extract_text_elements(
        mime_type=mime_type, data=file_data, file_name=file_name,
    )
    file_content = '\n\n'.join([str(el) for el in elements])

    if mime_type == 'text/csv':
        docs = [
            Document(
            page_content_key=content_key,
            page_content=t,
            metadata=metadata,
            ) for t in CSVTextSplitter(
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
            ) for t in SpacyTextSplitter(
                chunk_size=chunk_size,
            ).split_text(file_content)
        ]
    return docs
