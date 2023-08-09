import logging
import re

from django.http import HttpResponse
from rest_framework.exceptions import APIException

from apps.app_types import AppTypeFactory

logger = logging.getLogger(__name__)


class AuthorizationMiddleware:
    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'POST':
            discord_signature = request.headers.get('X-Signature-Ed25519')
            discord_timestamp = request.headers.get('X-Signature-Timestamp')
            slack_signature = request.headers.get('X-Slack-Signature')
            slack_timestamp = request.headers.get('X-Slack-Request-Timestamp')
            path = request.META['PATH_INFO']
            raw_body = request.body

            if ((discord_signature and discord_timestamp) or (slack_signature and slack_timestamp) or True) and re.match(r'^/api/apps/.*/run', path):
                app_id = path.split('/')[3]
                platform = path.split('/')[4]
                app, signature_verifier = AppTypeFactory.get_app_type_signature_verifier(
                    app_id, platform,
                )
                try:
                    signature_verifier(app, request.headers, raw_body)
                except APIException as e:
                    return HttpResponse(status=e.status_code)

                # Check with Discord app type

        return self.get_response(request)
