from django.contrib import admin

from .models import DataSource, DataSourceEntry, DataSourceEntryFiles, DataSourceType


class DataSourceEntryAdmin(admin.ModelAdmin):
    search_fields = ["uuid", "name", "datasource__name"]
    list_display = ["name"]


class DataSourceAdmin(admin.ModelAdmin):
    search_fields = ["uuid", "owner__email"]


admin.site.register(DataSourceEntry, DataSourceEntryAdmin)
admin.site.register(DataSourceType, DataSourceAdmin)
admin.site.register(DataSource)
admin.site.register(DataSourceEntryFiles)
