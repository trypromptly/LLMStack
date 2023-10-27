from django.urls import path

from . import apis

urlpatterns = [
    # Jobs
    path('api/jobs/app_run', apis.AppRunJobsViewSet.as_view({'get': 'list'})),
    path('api/jobs/app_run/<str:uid>', apis.AppRunJobsViewSet.as_view({'post': 'post'})),
]