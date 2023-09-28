from django.contrib import admin

from .models import DataSource
from .models import DataSourceEntry
from .models import DataSourceType


class DataSourceEntryAdmin(admin.ModelAdmin):
    search_fields = ['uuid', 'name', 'datasource__name']
    

class DataSourceAdmin(admin.ModelAdmin):
    search_fields = ['uuid', 'owner__email']


admin.site.register(DataSourceEntry, DataSourceEntryAdmin)
admin.site.register(DataSourceType, DataSourceAdmin)
admin.site.register(DataSource)
