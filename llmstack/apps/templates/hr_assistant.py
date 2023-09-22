from typing import List
from typing import Optional

from pydantic import Field

from .app_template_interface import AppTemplateInterface
from .app_template_interface import BaseSchema
from .app_template_interface import TemplatePage


class HrAssistantBasicSchema(BaseSchema):
    assistant_image: str = Field(
        title='Assistant Image', widget='file',
        description='Icon to show for the messages from assistant', path='config.assistant_image',
    )
    datasource: List[str] = Field(
        description='Select all HR policies to answer employee questions. Click on the icon to the right to add new data', widget='datasource', path='processors[0].config.datasource',
    )
    window_color: str = Field(
        title='Primary Color of HR Assistant',
        description='Color of the HR Assistant', widget='color', path='config.window_color',
    )


class HrAssistantTemplate(AppTemplateInterface):
    """
    HR Assistant Template
    """
    @staticmethod
    def slug() -> str:
        return 'hr-assistant'

    @staticmethod
    def pages() -> list:
        return [
            TemplatePage(
                title='Basic',
                description='Configure your HR Assistant',
                page_schema=HrAssistantBasicSchema,
            ),
        ]
