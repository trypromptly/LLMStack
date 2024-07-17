import json
import logging
import uuid
from typing import Optional

import requests
from django.test import RequestFactory
from pydantic import Field

from llmstack.common.utils.text_extract import ExtraParams, extract_text_elements
from llmstack.connections.apis import ConnectionsViewSet
from llmstack.data.sources.base import BaseSource, SourceDataDocument
from llmstack.data.sources.utils import create_source_document_asset

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
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [],
                "application/vnd.openxmlformats-officedocument.presentationml.presentation": [],
                "application/vnd.google-apps.presentation": [],
                "application/vnd.google-apps.document": [],
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
        documents = []
        for file in gdrive_files:
            mime_type, file_data = export_gdrive_file(kwargs.get("user"), file.name, file.mimeType, file.model_dump())
            data_uri = f"data:{mime_type};name={file.name};base64,{file_data}"
            id = str(uuid.uuid4())
            file_objref = create_source_document_asset(
                data_uri, datasource_uuid=kwargs.get("datasource_uuid", None), document_id=id
            )

            documents.append(
                SourceDataDocument(
                    id_=id,
                    name=file.name,
                    content=file_objref,
                    mimetype=mime_type,
                    metadata={"file_name": file.name, "source": file.name, "mime_type": mime_type},
                ),
            )
        return documents

    def process_document(self, document: SourceDataDocument) -> SourceDataDocument:
        text = extract_text_elements(
            mime_type=document.mimetype,
            data=document.content,
            file_name=document.name,
            extra_params=ExtraParams(openai_key=None),
        )
        return document.model_copy(update={"text": text})
