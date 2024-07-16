import logging
import os
from typing import List

import yaml
from django.conf import settings
from django.core.cache import cache

from llmstack.data.schemas import DataPipelineTemplate

logger = logging.getLogger(__name__)


def get_data_pipeline_from_yaml(yaml_file: str) -> dict:
    with open(yaml_file, "r") as f:
        yaml_dict = yaml.safe_load(f)
        return DataPipelineTemplate(**yaml_dict)


def get_data_pipelines_from_contrib() -> List[DataPipelineTemplate]:
    """
    Loads app templates from yaml files in settings.APP_TEMPLATES_DIR and caches them in memory.
    """
    cache.delete("data_pipelines")
    data_pipelines = cache.get("data_pipelines")
    if data_pipelines:
        return data_pipelines

    data_pipelines = []
    if not hasattr(settings, "DATA_PIPELINES_DIR"):
        return data_pipelines

    if isinstance(settings.DATA_PIPELINES_DIR, str):
        for file in os.listdir(settings.DATA_PIPELINES_DIR):
            if file.endswith(".yml"):
                data_pipeline = get_data_pipeline_from_yaml(
                    os.path.join(settings.DATA_PIPELINES_DIR, file),
                )
                if data_pipeline:
                    data_pipelines.append(data_pipeline)

    elif isinstance(settings.DATA_PIPELINES_DIR, list):
        for dir in settings.DATA_PIPELINES_DIR:
            if not os.path.isdir(dir) or not os.path.exists(dir):
                continue
            for file in os.listdir(dir):
                if file.endswith(".yml"):
                    data_pipeline = get_data_pipeline_from_yaml(os.path.join(dir, file))
                    if data_pipeline:
                        data_pipelines.append(data_pipeline)

    cache.set("data_pipelines", data_pipelines)

    return data_pipelines


def get_data_pipeline_template_by_slug(slug: str) -> DataPipelineTemplate:
    """
    Returns an app template by slug.
    """
    for data_pipeline_template in get_data_pipelines_from_contrib():
        if data_pipeline_template.slug == slug:
            return data_pipeline_template
    return None
