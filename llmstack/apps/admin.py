from django.contrib import admin

from .models import App
from .models import AppData
from .models import AppHub
from .models import AppRunGraphEntry
from .models import AppSession
from .models import AppSessionData
from .models import AppTemplate
from .models import AppTemplateCategory
from .models import AppType
from .models import TestCase
from .models import TestSet


class AppHubAdmin(admin.ModelAdmin):
    raw_id_fields = ['app']


admin.site.register(AppType)
admin.site.register(AppRunGraphEntry)
admin.site.register(App)
admin.site.register(AppData)
admin.site.register(AppSession)
admin.site.register(AppSessionData)
admin.site.register(AppTemplate)
admin.site.register(AppTemplateCategory)
admin.site.register(AppHub, AppHubAdmin)
admin.site.register(TestSet)
admin.site.register(TestCase)
