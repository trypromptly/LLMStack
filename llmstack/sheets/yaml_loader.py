import logging
import os
from functools import cache

import yaml
from django.conf import settings

logger = logging.getLogger(__name__)


@cache
def load_sheet_templates():
    sheet_templates = {}
    if not hasattr(settings, "SHEET_TEMPLATES_DIR"):
        return sheet_templates

    for dir in settings.SHEET_TEMPLATES_DIR:
        if not os.path.isdir(dir) or not os.path.exists(dir):
            continue
        for filename in os.listdir(dir):
            if filename.endswith(".yml"):
                with open(os.path.join(dir, filename), "r") as file:
                    template = yaml.safe_load(file)
                    sheet_templates[template["slug"]] = template

    return sheet_templates


def get_sheet_template_by_slug(slug: str):
    sheet_templates = load_sheet_templates()
    return sheet_templates.get(slug)
