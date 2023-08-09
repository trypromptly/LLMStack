import logging
import os

from django.http import HttpResponse
from django.template import Context
from django.template import Template

from django.conf import settings

logger = logging.getLogger(__name__)


def index(request):
    with open(os.path.join(settings.REACT_APP_DIR, 'build', 'index.html')) as f:
        template = Template(f.read())
        return HttpResponse(template.render(context=Context()))
