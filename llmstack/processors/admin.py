from django.contrib import admin

from .models import ApiBackend
from .models import ApiProvider
from .models import Endpoint
from .models import EndpointInvocationCount
from .models import Feedback
from .models import PromptHub
from .models import Request
from .models import Response
from .models import RunEntry
from .models import Share
from .models import ShareTag
from .models import VersionedEndpoint

admin.site.register(ApiProvider)
admin.site.register(ApiBackend)
admin.site.register(Endpoint)
admin.site.register(EndpointInvocationCount)
admin.site.register(VersionedEndpoint)
admin.site.register(Feedback)
admin.site.register(Request)
admin.site.register(Response)
admin.site.register(RunEntry)
admin.site.register(Share)
admin.site.register(ShareTag)
admin.site.register(PromptHub)
