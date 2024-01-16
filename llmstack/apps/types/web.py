from typing import List, Optional

from pydantic import Field

from llmstack.apps.types.app_type_interface import AppTypeInterface, BaseSchema


class WebAppConfigSchema(BaseSchema):
    input_template: str = Field(
        title="Page Content",
        default="",
        description="Content to show at the top of the App page before the input form",
        widget="richtext",
    )
    allowed_sites: List[str] = Field(
        title="Allowed Sites to Embed this App",
        default=[],
        description="List of domains that are allowed to embed this app. Leave empty to allow all sites.",
        advanced_parameter=True,
        hidden=True,
    )
    layout: Optional[str] = Field(
        title="Layout",
        description="Layout to use for the app page",
        widget="textarea",
    )


class WebApp(AppTypeInterface[WebAppConfigSchema]):
    @staticmethod
    def slug() -> str:
        return "web"

    @staticmethod
    def name() -> str:
        return "Web App"

    @staticmethod
    def description() -> str:
        return "Provides a web app that takes in a user input returns rendered output in the provided template"
