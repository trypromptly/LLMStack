import json
import logging
from typing import List, Optional

import requests
from django.test import RequestFactory
from pydantic import Field

from llmstack.base.models import Profile
from llmstack.common.blocks.data.store.vectorstore import Document
from llmstack.common.utils.splitter import CSVTextSplitter, SpacyTextSplitter
from llmstack.common.utils.text_extract import ExtraParams, extract_text_elements
from llmstack.connections.apis import ConnectionsViewSet
from llmstack.datasources.handlers.datasource_processor import (
    WEAVIATE_SCHEMA,
    DataSourceEntryItem,
    DataSourceProcessor,
    DataSourceSchema,
)
from llmstack.datasources.models import DataSource

logger = logging.getLogger(__name__)


class GoogleDocument(DataSourceSchema):
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


class GdriveFileSchema(DataSourceSchema):
    file: str = Field(
        ...,
        widget="gdrive",
        description="File to be processed",
        accepts={
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
        maxSize=10000000,
    )

    @staticmethod
    def get_content_key() -> str:
        return "content"

    @staticmethod
    def get_weaviate_schema(class_name: str) -> dict:
        return WEAVIATE_SCHEMA.safe_substitute(
            class_name=class_name,
            content_key=GdriveFileSchema.get_content_key(),
        )


class GdriveFileDataSource(DataSourceProcessor[GdriveFileSchema]):
    def __init__(self, datasource: DataSource):
        super().__init__(datasource)
        profile = Profile.objects.get(user=self.datasource.owner)
        self.openai_key = profile.get_vendor_key("openai_key")

    @staticmethod
    def name() -> str:
        return "gdrive_file"

    @staticmethod
    def slug() -> str:
        return "gdrive_file"

    @staticmethod
    def description() -> str:
        return "Gdrive file"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    def validate_and_process(self, data: dict) -> List[DataSourceEntryItem]:
        entry = GdriveFileSchema(**data)
        file_json_data = json.loads(entry.file)
        gdrive_files = list(
            map(lambda x: GoogleDocument(**x), file_json_data["files"]),
        )

        return list(
            map(
                lambda x: DataSourceEntryItem(
                    name=x.name,
                    data={
                        "mime_type": x.mimeType,
                        "file_name": x.name,
                        "file_data": {
                            **x.dict(),
                            "connection_id": file_json_data["connection_id"],
                        },
                    },
                ),
                gdrive_files,
            ),
        )

    def export_gdrive_file(self, data: DataSourceEntryItem):
        supportedExportDocsMimeTypes = {
            "application/vnd.google-apps.document": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.google-apps.spreadsheet": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.google-apps.presentation": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        }

        # Have some better way to get the access token
        request = RequestFactory().get(
            f'/api/connections/{data.data["file_data"]["connection_id"]}/access_token',
        )
        request.user = self.datasource.owner
        access_token = (
            ConnectionsViewSet()
            .get_access_token(
                request=request,
                uid=data.data["file_data"]["connection_id"],
            )
            .data["access_token"]
        )

        if data.data["mime_type"] in supportedExportDocsMimeTypes:
            exportMimeType = supportedExportDocsMimeTypes[data.data["mime_type"]]
            exportUrl = f"https://www.googleapis.com/drive/v3/files/{data.data['file_data']['id']}/export?mimeType={exportMimeType}"
            response = requests.get(
                exportUrl,
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
            )
            if response.status_code == 200:
                logger.info(
                    f"Exported file {data.data['file_name']} to {exportMimeType}",
                )
                return exportMimeType, response.content
            else:
                raise Exception(
                    f"Error exporting file {data.data['file_name']}",
                )
        else:
            response = requests.get(
                f"https://www.googleapis.com/drive/v3/files/{data.data['file_data']['id']}?alt=media",
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
            )
            if response.status_code == 200:
                logger.info(f"Downloaded file {data.data['file_name']}")
                return data.data["mime_type"], response.content
            else:
                raise Exception(
                    f"Error downloading file {data.data['file_name']}",
                )

    def get_data_documents(
        self,
        data: DataSourceEntryItem,
    ) -> Optional[DataSourceEntryItem]:
        logger.info(
            f"Processing file: {data.data['file_name']} mime_type: {data.data['mime_type']}",
        )
        mime_type, file_data = self.export_gdrive_file(data)
        file_text = "\n\n".join(
            [
                str(el)
                for el in extract_text_elements(
                    mime_type=mime_type,
                    data=file_data,
                    file_name=data.data["file_name"],
                    extra_params=ExtraParams(openai_key=self.openai_key),
                )
            ],
        )

        if data.data["mime_type"] == "text/csv":
            docs = [
                Document(
                    page_content_key=self.get_content_key(),
                    page_content=t,
                    metadata={
                        "source": data.data["file_name"],
                    },
                )
                for t in CSVTextSplitter(
                    chunk_size=2,
                    length_function=CSVTextSplitter.num_tokens_from_string_using_tiktoken,
                ).split_text(file_text)
            ]
        else:
            docs = [
                Document(
                    page_content_key=self.get_content_key(),
                    page_content=t,
                    metadata={
                        "source": data.data["file_name"],
                    },
                )
                for t in SpacyTextSplitter(
                    chunk_size=1500,
                ).split_text(file_text)
            ]

        return docs
