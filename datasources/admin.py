from django.contrib import admin

from .models import DataSource
from .models import DataSourceEntry
from .models import DataSourceType


admin.site.register(DataSourceEntry)
admin.site.register(DataSourceType)
admin.site.register(DataSource)
