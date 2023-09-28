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
class AppAdmin(admin.ModelAdmin):
    search_fields = ['name', 'uuid', 'published_uuid']
class AppTypeAdmin(admin.ModelAdmin):
    search_fields = ['name', 'slug']
class AppTemplateAdmin(admin.ModelAdmin):
    search_fields = ['name', 'slug']


class AppDataAdmin(admin.ModelAdmin):
    search_fields = ['app_uuid']

admin.site.register(AppType, AppTypeAdmin)
admin.site.register(AppRunGraphEntry)
admin.site.register(App, AppAdmin)
admin.site.register(AppData)
admin.site.register(AppSession)
admin.site.register(AppSessionData)
admin.site.register(AppTemplate)
admin.site.register(AppTemplateCategory)
admin.site.register(AppHub, AppHubAdmin)
admin.site.register(TestSet)
admin.site.register(TestCase)
