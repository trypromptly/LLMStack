import json
import logging
from typing import Optional

import requests
from django.test import RequestFactory
from pydantic import Field

from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.common.utils.splitter import CSVTextSplitter, SpacyTextSplitter
from llmstack.common.utils.text_extract import ExtraParams, extract_text_elements
from llmstack.connections.apis import ConnectionsViewSet
from llmstack.data.sources.base import BaseSource

logger = logging.getLogger(__name__)


def export_gdrive_file(user, file_name, mime_type, file_data):
    supportedExportDocsMimeTypes = {
        "application/vnd.google-apps.document": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.google-apps.spreadsheet": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.google-apps.presentation": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }

    # Have some better way to get the access token
    request = RequestFactory().get(
        f'/api/connections/{file_data["connection_id"]}/access_token',
    )
    request.user = user
    access_token = (
        ConnectionsViewSet().get_access_token(request=request, uid=file_data["connection_id"]).data["access_token"]
    )

    if mime_type in supportedExportDocsMimeTypes:
        exportMimeType = supportedExportDocsMimeTypes[mime_type]
        exportUrl = f"https://www.googleapis.com/drive/v3/files/{file_data['id']}/export?mimeType={exportMimeType}"
        response = requests.get(exportUrl, headers={"Authorization": f"Bearer {access_token}"})
        if response.status_code == 200:
            logger.info(f"Exported file {file_name} to {exportMimeType}")
            return exportMimeType, response.content
        else:
            raise Exception(
                f"Error exporting file {file_name}",
            )
    else:
        response = requests.get(
            f"https://www.googleapis.com/drive/v3/files/{file_data['id']}?alt=media",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if response.status_code == 200:
            logger.info(f"Downloaded file {file_name}")
            return mime_type, response.content
        else:
            raise Exception(f"Error downloading file {file_name}")


class GoogleDocument(BaseSource):
    description: Optional[str] = None
    embedUrl: Optional[str] = None
    iconUrl: Optional[str] = None
    id: str
    isShared: Optional[bool] = None
    lastEditedUtc: int
    mimeType: Optional[str] = None
    name: Optional[str] = None
    organizationDisplayName: Optional[str] = None
    serviceId: Optional[str] = None
    sizeBytes: Optional[int] = None
    url: Optional[str] = None


class GdriveFileSchema(BaseSource):
    file: str = Field(
        description="File to be processed",
        json_schema_extra={
            "widget": "file",
            "maxSize": 10000000,
            "maxFiles": 4,
            "accepts": {
                "application/pdf": [],
                "application/json": [],
                "audio/mpeg": [],
                "application/rtf": [],
                "text/plain": [],
                "text/csv": [],
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [],
                "application/vnd.openxmlformats-officedocument.presentationml.presentation": [],
                "application/vnd.google-apps.presentation": [],
                "application/vnd.google-apps.document": [],
                "application/vnd.google-apps.spreadsheet": [],
                "audio/mp3": [],
                "video/mp4": [],
                "video/webm": [],
            },
        },
    )

    @classmethod
    def slug(cls) -> str:
        return "gdrive_file"

    @classmethod
    def provider_slug(cls) -> str:
        return "promptly"

    def get_data_documents(self, **kwargs):
        file_json_data = json.loads(self.file)
        gdrive_files = list(map(lambda x: GoogleDocument(**x), file_json_data["files"]))
        docs = []
        for file in gdrive_files:
            mime_type, file_data = export_gdrive_file(kwargs.get("user"), file.name, file.mimeType, file.model_dump())
            file_text = "\n\n".join(
                [
                    str(el)
                    for el in extract_text_elements(
                        mime_type=mime_type,
                        data=file_data,
                        file_name=file.name,
                        extra_params=ExtraParams(openai_key=self.openai_key),
                    )
                ],
            )

            if mime_type == "text/csv":
                for document in [
                    Document(page_content_key=self.get_content_key(), page_content=t, metadata={"source": file.name})
                    for t in CSVTextSplitter(
                        chunk_size=2, length_function=CSVTextSplitter.num_tokens_from_string_using_tiktoken
                    ).split_text(file_text)
                ]:
                    docs.append(document)
            else:
                for document in [
                    Document(
                        page_content_key=self.get_content_key(),
                        page_content=t,
                        metadata={"source": file.name},
                    )
                    for t in SpacyTextSplitter(chunk_size=1500).split_text(file_text)
                ]:
                    docs.append(document)

        return docs
