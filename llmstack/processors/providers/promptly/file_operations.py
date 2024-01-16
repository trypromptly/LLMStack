import logging
import os
import shutil
import tempfile
import uuid
from typing import Optional

from asgiref.sync import async_to_sync
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import storages
from pydantic import Field

from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface, ApiProcessorSchema)

generatedfiles_storage = storages["generatedfiles"]

logger = logging.getLogger(__name__)


class FileOperationsInput(ApiProcessorSchema):
    content: str = Field(
        default="",
        description="The contents of the file. Skip this field if you want to create an archive of the directory",
    )
    filename: Optional[str] = Field(
        description="The name of the file to create. If not provided, a random name will be generated",
    )
    directory: Optional[str] = Field(
        description="The directory to create the file in. If not provided, the file will be created in a temporary directory and path is returned",
    )
    archive: bool = Field(
        default=False,
        description="If true, an archive with the contents of the directory will be created",
    )


class FileOperationsOutput(ApiProcessorSchema):
    directory: str = Field(description="The directory the file was created in")
    filename: str = Field(description="The name of the file created")
    url: str = Field(description="Download URL of the file created")
    archive: bool = Field(
        default=False,
        description="If true, then we just created an archive with contents from directory",
    )
    text: str = Field(
        default="",
        description="Textual description of the output",
    )


class FileOperationsConfiguration(ApiProcessorSchema):
    pass


class FileOperationsProcessor(
    ApiProcessorInterface[FileOperationsInput, FileOperationsOutput, FileOperationsConfiguration],
):
    @staticmethod
    def name() -> str:
        return "File Operations"

    @staticmethod
    def slug() -> str:
        return "file_operations"

    @staticmethod
    def description() -> str:
        return "Creates files, directories and archives with provided content"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    @staticmethod
    def tool_only() -> bool:
        return True

    def _copy_directory(self, directory, temp_archive_dir):
        """
        Recursively copies the django's storage directory to a temporary directory
        """
        if not generatedfiles_storage.exists(
            directory,
        ) or not os.path.exists(temp_archive_dir):
            return

        files = generatedfiles_storage.listdir(directory)[1]
        directories = generatedfiles_storage.listdir(directory)[0]

        # Copy the files to the temporary directory by reading their contents
        for file in files:
            with generatedfiles_storage.open(f"{directory}/{file}", "rb") as f:
                with open(f"{temp_archive_dir}/{file}", "wb") as temp_file:
                    temp_file.write(f.read())

        # Recursively copy the directories to the temporary directory
        for subdirectory in directories:
            # Make a directory
            os.mkdir(f"{temp_archive_dir}/{subdirectory}")
            self._copy_directory(
                f"{directory}/{subdirectory}",
                f"{temp_archive_dir}/{subdirectory}",
            )

    def _create_archive(self, file):
        """
        Using django storage, recursively copies all the files to a temporary directory and creates an archive
        """
        # Create a temporary directory to store the archive
        with tempfile.TemporaryDirectory() as temp_archive_dir:
            if generatedfiles_storage.exists(file):
                self._copy_directory(file, temp_archive_dir)

            # Create a temporary file to store the archive
            temp_archive_file = tempfile.NamedTemporaryFile()

            # Create the archive
            shutil.make_archive(
                temp_archive_file.name,
                "zip",
                temp_archive_dir,
            )

            temp_archive_file.close()

            # Copy archive to storage
            return generatedfiles_storage.save(
                f"{file}.zip",
                ContentFile(
                    open(f"{temp_archive_file.name}.zip", "rb").read(),
                ),
            )

    def process(self) -> dict:
        output_stream = self._output_stream

        content = self._input.content
        filename = self._input.filename or str(uuid.uuid4())
        directory = self._input.directory or str(uuid.uuid4())
        archive = self._input.archive

        # Create an archive if directory is provided but not content with
        # archive flag set
        if not content and archive:
            saved_path = self._create_archive(directory)
            generated_url = generatedfiles_storage.url(saved_path)
            url = (
                f"{settings.SITE_URL}{generated_url}"
                if generated_url.startswith(
                    "/",
                )
                and settings.SITE_URL
                else generated_url
            )
            text = f"Archive created at {url} with contents from directory {directory}"

            async_to_sync(output_stream.write)(
                FileOperationsOutput(
                    directory=directory,
                    filename=os.path.basename(saved_path),
                    url=url,
                    archive=True,
                    text=text,
                ),
            )
        elif content and not archive:
            saved_path = generatedfiles_storage.save(
                f"{directory}/{filename}",
                ContentFile(content),
            )
            generated_url = generatedfiles_storage.url(saved_path)
            url = (
                f"{settings.SITE_URL}{generated_url}"
                if generated_url.startswith(
                    "/",
                )
                and settings.SITE_URL
                else generated_url
            )
            filename = os.path.basename(saved_path)
            text = f"File {filename} created at {url} in directory {directory}"

            async_to_sync(output_stream.write)(
                FileOperationsOutput(
                    directory=directory,
                    filename=filename,
                    url=url,
                    archive=False,
                    text=text,
                ),
            )

        # Finalize the output stream
        output = output_stream.finalize()
        return output
