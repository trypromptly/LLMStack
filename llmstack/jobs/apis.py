import logging 
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response as DRFResponse
from django.views.decorators.csrf import csrf_exempt

from llmstack.apps.apis import AppViewSet

logger = logging.getLogger(__name__)

class JobsViewSet(viewsets.ViewSet):
    
    def get_permissions(self):
        return [AllowAny()]
        if self.action == 'submit_job':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @csrf_exempt
    def app_run_job(self, request):
        data = request.data
        published_app_id = data.get('published_app_id')
        app = AppViewSet().getByPublishedUUID(request=request, published_app_id=published_app_id)
        app_input = data.get('app_input')
        logger.info(f"submit_app_run_job app: {app}")
        return DRFResponse(status=204)
    