from typing import List, Type, TypeVar
from pydantic import BaseModel

from llmstack.common.utils.utils import get_ui_schema_from_jsonschema

AppTemplateSchemaType = TypeVar('AppTemplateSchemaType')


class BaseSchema(BaseModel):
    @classmethod
    def get_schema(cls):
        return super().schema()

    @classmethod
    def get_ui_schema(cls):
        return get_ui_schema_from_jsonschema(cls.get_schema())


class TemplatePage(BaseModel):
    title: str
    description: str
    page_schema: Type

    def get_schema(self) -> dict:
        return self.page_schema.get_schema()

    def get_ui_schema(self) -> dict:
        return get_ui_schema_from_jsonschema(self.page_schema.get_schema())

    def get_page_schema(self) -> dict:
        return {
            'title': self.title,
            'description': self.description,
            'schema': self.get_schema(),
            'ui_schema': self.get_ui_schema(),
        }


class AppTemplateInterface:
    """
    This is the interface for all app templates.
    """
    @staticmethod
    def slug(self) -> str:
        raise NotImplementedError

    @staticmethod
    def pages(self) -> List[TemplatePage]:
        raise NotImplementedError

    @classmethod
    def get_pages_schema(cls) -> List:
        """
        Returns a list of TemplatePage schemas.
        """
        return [page.get_page_schema() for page in cls.pages()]
