"""
Utils to convert yaml to App and AppTemplate schema models and vice versa
"""
import yaml
import os
from django.conf import settings
from django.core.cache import cache
from typing import List, Type
from pydantic import BaseModel, Field, create_model
from apps.schemas import AppTemplate

from common.blocks.base.schema import get_ui_schema_from_json_schema


def get_input_model_from_fields(name: str, input_fields: list) -> Type['BaseModel']:
    """
    Dynamically creates a Pydantic model from a list of input fields.

    Args:
        name (str): The name of the model to be created.
        input_fields (list): A list of dictionaries representing the input fields of the model.

    Returns:
        Type['BaseModel']: The dynamically created Pydantic model.
    """
    return create_model(
        f'{name}', **{field['name']: (int if field['type'] == 'int' else str, Field(**{k: field[k] for k in field})) for field in input_fields})


def get_app_template_from_yaml(yaml_file: str) -> dict:
    """
    Reads a YAML file and returns a dictionary containing the app template.

    Args:
        yaml_file (str): The path to the YAML file.

    Returns:
        dict: A dictionary containing the app template.
    """
    with open(yaml_file, 'r') as f:
        yaml_dict = yaml.safe_load(f)

        # Construct dynamic models for app template page input and app input
        pages = yaml_dict.get('pages', [])
        for page in pages:
            input_fields = page.get('input_fields', [])
            input_model = get_input_model_from_fields(
                page["title"], input_fields)
            page['input_schema'] = input_model.schema()
            page['input_ui_schema'] = get_ui_schema_from_json_schema(
                input_model.schema())
            page.pop('input_fields')

        app = yaml_dict.get('app', {})
        input_fields = app.get('input_fields', [])
        input_model = get_input_model_from_fields(
            app["name"], input_fields)
        app['input_schema'] = input_model.schema()
        app['input_schema'].pop('title')
        app['input_ui_schema'] = get_ui_schema_from_json_schema(
            input_model.schema())
        app.pop('input_fields')

        return AppTemplate(**yaml_dict)


def get_app_templates_from_contrib() -> List[AppTemplate]:
    """
    Loads app templates from yaml files in settings.APP_TEMPLATES_DIR and caches them in memory.
    """
    app_templates = cache.get('app_templates')
    if app_templates:
        return app_templates

    app_templates = []
    if not hasattr(settings, 'APP_TEMPLATES_DIR'):
        return app_templates

    for file in os.listdir(settings.APP_TEMPLATES_DIR):
        if file.endswith('.yml'):
            app_template = get_app_template_from_yaml(
                os.path.join(settings.APP_TEMPLATES_DIR, file))
            if app_template:
                app_templates.append(app_template)
    cache.set('app_templates', app_templates)

    return app_templates


def get_app_template_by_slug(slug: str) -> dict:
    """
    Returns an app template by slug.
    """
    for app_template in get_app_templates_from_contrib():
        if app_template.slug == slug:
            return app_template
    return None
