from typing import List
from typing import Optional

from pydantic import Field

from .app_template_interface import AppTemplateInterface
from .app_template_interface import BaseSchema
from .app_template_interface import TemplatePage


class AIAugmentedSearchBasicSchema(BaseSchema):
    result_count: int = Field(
        title='Number of Results',
        description='Number of search results to show',
        path='processors[0].config.k',
        default=10,
    )
    show_ai_answer: bool = Field(
        title='Show AI Answer',
        description='Let AI answer the user question along with displaying the search results',
        path='processors[0].config.generate_answer',
        default=True,
    )
    datasource: List[str] = Field(
        description='Datasources to search',
        widget='datasource',
        path='processors[0].config.datasources',
    )


class AIAugmentedSearchTemplate(AppTemplateInterface):
    """
    AI Augmented Search Template
    """
    @staticmethod
    def slug() -> str:
        return 'ai-augmented-search'

    @staticmethod
    def pages() -> list:
        return [
            TemplatePage(
                title='Settings',
                description='Configure your AI search parameters',
                page_schema=AIAugmentedSearchBasicSchema,
            ),
        ]
