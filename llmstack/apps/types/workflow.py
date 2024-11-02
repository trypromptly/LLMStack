from typing import List, Literal, Optional, Union

from pydantic import Field

from llmstack.apps.types.app_type_interface import AppTypeInterface, BaseSchema


class WebAppRenderer(BaseSchema):
    renderer_slug: Literal["web"] = Field(
        default="web",
        json_schema_extra={"readOnly": True},
    )


class ChatAppRenderer(BaseSchema):
    renderer_slug: Literal["chat"] = Field(
        default="chat",
        json_schema_extra={"readOnly": True},
    )
    suggested_messages: List[str] = Field(
        title="Suggested messages",
        default=[],
        description="List of upto 3 suggested messages to show to the user",
    )
    window_color: str = Field(
        title="Primary Color of Chat Window",
        default="#477195",
        description="Color of the chat window",
        json_schema_extra={"widget": "color", "advanced_parameter": True},
    )
    chat_bubble_text: Optional[str] = Field(
        default=None,
        title="App Bubble Text",
        description="Text to show in the app bubble when embedded in another page. If not provided, it shows chat bubble icon.",
        json_schema_extra={"advanced_parameter": True},
    )
    chat_bubble_style: Optional[str] = Field(
        default=None,
        title="App Bubble Style",
        description="CSS style object to apply to the app bubble when embedded in another page",
        json_schema_extra={"widget": "textarea", "advanced_parameter": True},
    )


class WorkflowConfigSchema(BaseSchema):
    input_template: str = Field(
        title="",
        default="",
        description="Content to show at the top of the App page before the input form",
        json_schema_extra={"widget": "richtext", "advanced_parameter": True},
    )
    layout: Optional[str] = Field(
        default=None,
        title="Layout",
        description="Advanced layout to use for the workflow",
        json_schema_extra={"widget": "hidden"},
    )
    renderer_settings: Union[ChatAppRenderer, WebAppRenderer] = Field(
        default=None,
        title="Renderer Type",
        description="Type of renderer to use for the workflow",
    )


class Workflow(AppTypeInterface[WorkflowConfigSchema]):
    @staticmethod
    def slug() -> str:
        return "workflow"

    @staticmethod
    def name() -> str:
        return "Workflow"

    @staticmethod
    def description() -> str:
        return "Takes in a user input, processes it through a series of processors, and returns a rendered output."
