from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

"""
This file contains YAML schemas for the apps and app templates.
"""


class InputField(BaseModel):
    advanced_parameter: Optional[bool] = None
    default: Optional[Any] = None
    description: Optional[str] = None
    enum: Optional[List[Any]] = None
    enumNames: Optional[List[str]] = None
    format: Optional[str] = None
    items: Optional[Dict[str, Any]] = None
    maximum: Optional[int] = None
    minimum: Optional[int] = None
    multipleOf: Optional[int] = None
    name: str
    path: Optional[str] = None
    pattern: Optional[str] = None
    required: Optional[bool] = None
    title: str
    type: str = "string"
    widget: Optional[str] = None
    options: Optional[List[Any]] = None


class OutputTemplate(BaseModel):
    """
    OutputTemplate schema
    """

    markdown: str = Field(None, description="Markdown template for output")
    jsonpath: Optional[str] = Field(
        default=None,
    )


class Provider(BaseModel):
    """
    Provider schema
    """

    name: str = Field(None, description="Name of the provider")
    slug: str = Field(
        None,
        description="Unique slug for the provider. Must be @github username for individual contributions",
    )
    description: str = Field(None, description="Description of the provider")


class Processor(BaseModel):
    """
    Processor schema
    """

    id: str = Field(
        None,
        description="Unique identifier for the processor in the app run graph",
    )
    name: str = Field(None, description="Name of the processor")
    description: str = Field(None, description="Description of the processor")
    provider_slug: str = Field(
        None,
        description="Slug of the processor provider",
    )
    processor_slug: str = Field(None, description="Slug of the processor")
    # TODO: Validate input and config against backing processor's schemas
    input: dict = Field(None, description="Input for the processor")
    config: dict = Field(None, description="Configuration for the processor")
    output_template: dict = Field(
        None,
        description="Output template for the processor",
    )


class App(BaseModel):
    """
    App schema
    """

    name: str = Field(None, description="Name of the app")
    slug: str = Field(None, description="Unique slug for the app")
    type_slug: str = Field(None, description="Slug of the app type")
    description: str = Field(None, description="Description of the app")
    config: Optional[dict] = Field(
        default=None,
        description="Configuration for the app",
    )
    input_fields: Optional[List[InputField]] = Field(
        default=None,
        description="Input fields for the app",
    )
    input_schema: Optional[dict] = Field(
        default=None,
        description="Input schema for the app",
    )
    input_ui_schema: Optional[dict] = Field(
        default=None,
        description="Input UI schema for the app",
    )
    output_template: OutputTemplate = Field(
        default=None,
        description="Output template for the app",
    )
    processors: List[Processor] = Field(
        default=None,
        description="Processors for the app",
    )


class AppTemplatePage(BaseModel):
    """
    AppTemplatePage schema
    """

    title: str = Field(None, description="Title of the page")
    description: str = Field(None, description="Description of the page")
    input_fields: Optional[List[InputField]] = Field(
        default=None,
        description="Input fields for the page",
    )
    input_schema: Optional[dict] = Field(
        default=None,
        description="Schema for the page",
    )
    input_ui_schema: Optional[dict] = Field(
        default=None,
        description="UI schema for the page",
    )


class AppTemplate(BaseModel):
    """
    AppTemplate schema
    """

    name: str = Field(None, description="Name of the app template")
    slug: str = Field(None, description="Unique slug for the app template")
    icon: str = Field(None, description="Icon for the app template")
    category_slugs: List[str] = Field(
        None,
        description="Slugs of the app template categories",
    )
    description: str = Field(
        None,
        description="Description of the app template",
    )
    pages: List[AppTemplatePage] = Field(
        None,
        description="Pages of the app template",
    )
    app: App = Field(None, description="App of the app template")
