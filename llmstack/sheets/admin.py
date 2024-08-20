from django.contrib import admin

from .models import PromptlySheet, PromptlySheetFiles, PromptlySheetRunEntry

# Register your models here.
admin.site.register(PromptlySheet)
admin.site.register(PromptlySheetRunEntry)
admin.site.register(PromptlySheetFiles)
