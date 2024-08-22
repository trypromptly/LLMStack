import base64
import logging
import re
from io import BytesIO
from typing import List, Optional

from striprtf.striprtf import rtf_to_text
from unstructured.documents.elements import Element, ElementMetadata, Text
from unstructured.partition.auto import partition_html
from unstructured.partition.docx import partition_docx
from unstructured.partition.epub import partition_epub
from unstructured.partition.image import partition_image
from unstructured.partition.md import partition_md
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.pptx import partition_pptx
from unstructured.partition.text import partition_text
from unstructured.partition.xlsx import partition_xlsx

from llmstack.common.utils.audio_loader import (
    partition_audio,
    partition_video,
    partition_youtube_audio,
)
from llmstack.common.utils.crawlers import run_url_spider_in_process

from . import prequests as requests

logger = logging.getLogger(__name__)
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Windows; Windows x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36",
}
timeout = 100


class ExtraParams:
    def __init__(
        self,
        openai_key=None,
        azure_openai_key=None,
        youtube_api_key=None,
        connection=None,
    ):
        self._openai_key = openai_key
        self._youtube_api_key = youtube_api_key
        self._azure_openai_key = azure_openai_key
        self._connection = connection

    @property
    def openai_key(self):
        return self._openai_key

    @property
    def azure_openai_key(self):
        return self._azure_openai_key

    @property
    def connection(self):
        return self._connection


def get_url_content_type(url, connection=None):
    response = requests.head(
        url,
        allow_redirects=True,
        verify=False,
        _connection=connection,
    )

    content_type = response.headers.get("Content-Type", "")
    return content_type


def is_youtube_video_url(url):
    youtube_regex = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=)?([a-zA-Z0-9_-]{11})"
    match = re.match(youtube_regex, url)
    return match is not None


def extract_text_elements(
    mime_type,
    data,
    file_name,
    charset="utf-8",
    chunking_strategy="basic",  # supported 'basic' or 'by_title'
    extra_params: Optional[ExtraParams] = None,
) -> List[Element]:
    data_fp = BytesIO(data)
    elements = []
    if mime_type == "application/pdf":
        elements = partition_pdf(file=data_fp, chunking_strategy=chunking_strategy)
    elif mime_type == "application/rtf" or mime_type == "text/rtf":
        elements = partition_text(text=rtf_to_text(data.decode(charset)), chunking_strategy=chunking_strategy)
    elif mime_type == "text/plain":
        elements = partition_text(text=data.decode(charset), chunking_strategy=chunking_strategy)
    elif mime_type == "application/json":
        elements = [
            Text(
                text=data.decode(charset),
                metadata=ElementMetadata(filename=file_name),
            ),
        ]
    elif mime_type == "text/csv" or mime_type == "application/csv":
        elements = [
            Text(
                text=data.decode(charset),
                metadata=ElementMetadata(filename=file_name),
            ),
        ]
    elif mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        elements = partition_xlsx(file=data_fp, chunking_strategy=chunking_strategy)
    elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        elements = partition_docx(file=data_fp, chunking_strategy=chunking_strategy)
    elif mime_type == "application/msword":
        raise Exception(
            "Unsupported file type .doc please convert it to .docx",
        )
    elif mime_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
        elements = partition_pptx(file=data_fp, chunking_strategy=chunking_strategy)
    elif mime_type == "application/vnd.ms-powerpoint":
        raise Exception(
            "Unsupported file type .ppt please convert it to .pptx",
        )
    elif mime_type == "image/jpeg" or mime_type == "image/png":
        elements = partition_image(file=data_fp)
    elif mime_type == "audio/mpeg" or mime_type == "audio/mp3":
        audio_text = "\n\n".join(
            partition_audio(
                data,
                mime_type=mime_type,
                openai_key=extra_params.openai_key,
                file_name=file_name,
            ),
        )
        elements = [
            Text(
                text=audio_text,
                metadata=ElementMetadata(filename=file_name),
            ),
        ]
    elif mime_type == "video/mp4" or mime_type == "video/mpeg":
        video_text = "\n\n".join(
            partition_video(
                data,
                mime_type=mime_type,
                openai_key=extra_params.openai_key,
                file_name=file_name,
            ),
        )
        elements = [
            Text(
                text=video_text,
                metadata=ElementMetadata(filename=file_name),
            ),
        ]
    elif mime_type == "video/webm":
        video_text = "\n\n".join(
            partition_video(
                data,
                mime_type=mime_type,
                openai_key=extra_params.openai_key,
                file_name=file_name,
            ),
        )
        elements = [
            Text(
                text=video_text,
                metadata=ElementMetadata(filename=file_name),
            ),
        ]
    elif mime_type == "text/html":
        elements = partition_html(file=data_fp, headers=headers, chunking_strategy=chunking_strategy)
    elif mime_type == "application/epub+zip":
        elements = partition_epub(file=data_fp, chunking_strategy=chunking_strategy)
    elif mime_type == "text/markdown":
        elements = partition_md(text=data.decode(charset), chunking_strategy=chunking_strategy)
    else:
        raise Exception("Unsupported file type")

    # Merge elements depending on metadata page number
    merged_elements = []
    for element in elements:
        if len(merged_elements) == 0:
            merged_elements.append(element)
        else:
            if element.metadata.page_number == merged_elements[-1].metadata.page_number:
                merged_elements[-1].text += f"\n{element.text}"
            else:
                merged_elements.append(element)
    return merged_elements


def extract_text_from_b64_json(
    mime_type,
    base64_encoded_data,
    file_name="filename",
    extra_params=None,
):
    decoded_data = base64.b64decode(base64_encoded_data)
    elements = extract_text_elements(
        mime_type=mime_type,
        data=decoded_data,
        file_name=file_name,
        extra_params=extra_params,
    )
    return "\n\n".join([str(el) for el in elements])


def extract_text_from_url(url, extra_params: Optional[ExtraParams] = None):
    if is_youtube_video_url(url):
        # Get Youtube video content from URL parse the content and return the
        # text
        text = "\n\n".join(
            partition_youtube_audio(
                url=url,
                openai_key=extra_params.openai_key,
            ),
        )
        return text

    url_content_type = get_url_content_type(
        url=url,
        connection=extra_params.connection,
    )
    url_content_type_parts = url_content_type.split(";")
    mime_type = url_content_type_parts[0]
    url_content_type_args = {}

    for part in url_content_type_parts[1:]:
        key, value = part.split("=")
        url_content_type_args[key.strip().rstrip()] = value.strip().rstrip().lower()

    data = None
    if mime_type == "text/html":
        try:
            result = run_url_spider_in_process(
                url=url,
                use_renderer=True,
                connection=extra_params.connection,
            )
            data = result[0]["html_page"].encode("utf-8")
        except BaseException:
            logger.exception("Error in running url spider")
            data = requests.get(
                url=url,
                headers=headers,
                timeout=timeout,
                _connection=extra_params.connection,
            ).content
    else:
        data = requests.get(
            url=url,
            headers=headers,
            timeout=timeout,
            _connection=extra_params.connection,
        ).content

    elements = extract_text_elements(
        mime_type=mime_type,
        data=data,
        file_name=url.split("/")[-1],
        charset=url_content_type_args.get(
            "charset",
            "utf-8",
        ),
        extra_params=extra_params,
    )
    return "\n\n".join([str(el) for el in elements])
