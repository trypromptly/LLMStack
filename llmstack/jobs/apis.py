import logging 
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response as DRFResponse
from django.views.decorators.csrf import csrf_exempt

from llmstack.apps.apis import AppViewSet

logger = logging.getLogger(__name__)

def run_app(app_id, input_data):
    logger.info(f"run_app app_id: {app_id}, input_data: {input_data}")
    return True

class JobsViewSet(viewsets.ViewSet):
    
    def get_permissions(self):
        if self.action == 'submit_job':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @csrf_exempt
    def app_run_job(self, request):
        data = request.data
        published_app_id = data.get('published_app_id')
        app = AppViewSet().getByPublishedUUID(request=request, published_uuid=published_app_id)        
        return DRFResponse(status=204)
    