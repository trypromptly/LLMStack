from django.urls import path

from . import apis

urlpatterns = [
    # Jobs
    path('api/jobs', apis.JobsViewSet.as_view({'get': 'list'})),
    path('api/jobs/<str:uid>', apis.JobsViewSet.as_view({'get': 'get', 'delete': 'delete'})),
    path('api/jobs/<str:uid>/pause', apis.JobsViewSet.as_view({'post': 'pause'})),
    path('api/jobs/<str:uid>/resume', apis.JobsViewSet.as_view({'post': 'resume'})),
    
    # App run jobs
    path('api/jobs/app_run', apis.AppRunJobsViewSet.as_view({'post': 'post'})),
    path('api/jobs/app_run/<str:uid>', apis.AppRunJobsViewSet.as_view({'get': 'get', 'delete': 'delete'})),
    path('api/jobs/app_run/<str:uid>/pause', apis.AppRunJobsViewSet.as_view({'post': 'pause'})),
    path('api/jobs/app_run/<str:uid>/resume', apis.AppRunJobsViewSet.as_view({'post': 'resume'})),
    # Data source jobs
    path('api/jobs/datasource_refresh', apis.DataSourceRefreshJobsViewSet.as_view({'post': 'post'})),
    path('api/jobs/datasource_refresh/<str:uid>', apis.DataSourceRefreshJobsViewSet.as_view({'post': 'post', 'get': 'get', 'delete': 'delete'})),
    path('api/jobs/datasource_refresh/<str:uid>/pause', apis.DataSourceRefreshJobsViewSet.as_view({'post': 'pause'})),
    path('api/jobs/datasource_refresh/<str:uid>/resume', apis.DataSourceRefreshJobsViewSet.as_view({'post': 'resume'})),
]