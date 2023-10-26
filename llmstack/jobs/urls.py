from django.urls import path

from . import apis

urlpatterns = [
    # Jobs
    path('api/jobs/app_run', apis.JobsViewSet.as_view({'post': 'app_run_submit'})),
]