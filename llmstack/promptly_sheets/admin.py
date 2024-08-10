from django.contrib import admin

from .models import PromptlySheet, PromptlySheetCell

# Register your models here.
admin.site.register(PromptlySheet)
admin.site.register(PromptlySheetCell)
