from django.urls import path

from . import apis

urlpatterns = [
     # App run jobs
    path('api/jobs/app_run', apis.AppRunJobsViewSet.as_view({'post': 'create'})),
    
    # Data source jobs
    path('api/jobs/datasource_refresh', apis.DataSourceRefreshJobsViewSet.as_view({'post': 'create'})),

    # Jobs
    path('api/jobs', apis.JobsViewSet.as_view({'get': 'list'})),
    path('api/jobs/<str:uid>', apis.JobsViewSet.as_view({'get': 'get', 'delete': 'delete'})),
    path('api/jobs/<str:uid>/pause', apis.JobsViewSet.as_view({'post': 'pause'})),
    path('api/jobs/<str:uid>/resume', apis.JobsViewSet.as_view({'post': 'resume'})),
]