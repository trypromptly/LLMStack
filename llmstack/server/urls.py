from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("llmstack.apps.urls")),
    path("", include("llmstack.assets.urls")),
    path("", include("llmstack.processors.urls")),
    path("", include("llmstack.organizations.urls")),
    path("", include("llmstack.data.urls")),
    path("", include("llmstack.connections.urls")),
    path("", include("llmstack.jobs.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.GENERATEDFILES_ROOT and settings.GENERATEDFILES_URL:
    urlpatterns += static(
        settings.GENERATEDFILES_URL,
        document_root=settings.GENERATEDFILES_ROOT,
    )

if settings.ADMIN_ENABLED:
    urlpatterns += [path("admin/", admin.site.urls)]

    admin.site.site_header = "LLMStack"
    admin.site.site_title = "LLMStack"
    admin.site.index_title = "LLMStack Administration"

urlpatterns += [path("", include("llmstack.base.urls"))]
