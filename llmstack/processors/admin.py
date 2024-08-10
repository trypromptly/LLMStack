from django.contrib import admin

from .models import (
    ApiBackend,
    ApiProvider,
    Endpoint,
    Feedback,
    RunEntry,
    ShareTag,
    VersionedEndpoint,
)

admin.site.register(ApiProvider)
admin.site.register(ApiBackend)
admin.site.register(Endpoint)
admin.site.register(VersionedEndpoint)
admin.site.register(Feedback)
admin.site.register(RunEntry)
admin.site.register(ShareTag)
