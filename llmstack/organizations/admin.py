from django.contrib import admin

from .models import Organization, OrganizationSettings

admin.site.register(Organization)
admin.site.register(OrganizationSettings)
