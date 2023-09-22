import os
import re
from pydantic import root_validator

from llmstack.common.blocks.base.processor import ProcessorInterface
from llmstack.common.blocks.data import DataDocument
from llmstack.common.blocks.data.source import DataSourceInputSchema, DataSourceConfigurationSchema, DataSourceOutputSchema


class DirectoryTextLoaderInputSchema(DataSourceInputSchema):
    directory: str
    recursive: bool = False

    @root_validator()
    @classmethod
    def validate_directory(cls, field_values) -> str:
        value = field_values.get("directory")
        recursive = field_values.get("recursive")

        # TODO: Validate that directory is a valid directory path and the directory exists
        if not re.match(r"^[a-zA-Z0-9_\-\.\/]+$", value):
            raise ValueError("Directory must be a valid string")

        return value


class DirectoryTextLoader(ProcessorInterface[DirectoryTextLoaderInputSchema, DataSourceOutputSchema, DataSourceConfigurationSchema]):

    def process(self, input: DirectoryTextLoaderInputSchema, configuration: DataSourceConfigurationSchema) -> DataSourceOutputSchema:
        result = []
        files = []
        # If recursive is true, then we need to recursively walk the directory
        if input.recursive:
            for dir, dirname, filename in os.walk(input.directory):
                files.extend(filename)
        else:
            files = os.listdir(input.directory)

        for file in files:
            with open(os.path.join(input.directory, file), "r") as f:
                result.append(DataDocument(name=file, content=f.read()))

        return DataSourceOutputSchema(documents=result)
