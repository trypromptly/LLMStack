import logging

from django.http import Http404

logger = logging.getLogger(__name__)


def app_index(request, app_id):
    Http404("Not found")
