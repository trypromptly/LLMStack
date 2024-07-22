from django.contrib import admin

from .models import AppStoreApp, AppStoreAppAssets

admin.site.register(AppStoreApp)
admin.site.register(AppStoreAppAssets)
