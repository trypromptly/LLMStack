from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include
from django.urls import path

urlpatterns = [
    path('', include('apps.urls')),
    path('', include('processors.urls')),
    path('', include('organizations.urls')),
    path('', include('datasources.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.ADMIN_ENABLED:
    urlpatterns += [path('admin/', admin.site.urls)]

    admin.site.site_header = 'LLMStack'
    admin.site.site_title = 'LLMStack'
    admin.site.index_title = 'LLMStack Administration'

urlpatterns += [path('', include('base.urls'))]
