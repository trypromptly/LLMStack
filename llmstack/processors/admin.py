from django.contrib import admin

from .models import (
    ApiBackend,
    ApiProvider,
    Endpoint,
    Feedback,
    Request,
    Response,
    RunEntry,
    ShareTag,
    VersionedEndpoint,
)

admin.site.register(ApiProvider)
admin.site.register(ApiBackend)
admin.site.register(Endpoint)
admin.site.register(VersionedEndpoint)
admin.site.register(Feedback)
admin.site.register(Request)
admin.site.register(Response)
admin.site.register(RunEntry)
admin.site.register(ShareTag)
