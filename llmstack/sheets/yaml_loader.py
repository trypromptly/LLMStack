import logging
import os
from functools import cache

import yaml
from django.conf import settings

logger = logging.getLogger(__name__)


@cache
def load_sheet_templates():
    sheet_templates = {}
    logger.info(settings.SHEET_TEMPLATES_DIR)
    if not hasattr(settings, "SHEET_TEMPLATES_DIR"):
        logger.info("No sheet templates dir found")
        return sheet_templates

    for dir in settings.SHEET_TEMPLATES_DIR:
        if not os.path.isdir(dir) or not os.path.exists(dir):
            logger.info(f"No sheet templates dir found at {dir}")
            continue
        logger.info(f"Loading sheet templates from {dir}")
        for filename in os.listdir(dir):
            logger.info(f"Loading sheet template {filename}")
            if filename.endswith(".yml"):
                logger.info(f"Loading sheet template {filename}")
                with open(os.path.join(dir, filename), "r") as file:
                    template = yaml.safe_load(file)
                    logger.info(f"Loaded sheet template {template}")
                    sheet_templates[template["slug"]] = template

    logger.info(f"Loaded {len(sheet_templates.values())} sheet templates")
    return sheet_templates


def get_sheet_template_by_slug(slug: str):
    sheet_templates = load_sheet_templates()
    return sheet_templates.get(slug)
