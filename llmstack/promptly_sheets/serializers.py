from rest_framework import serializers

from llmstack.promptly_sheets.models import PromptlySheet, PromptlySheetCell


class PromptlySheetSeializer(serializers.ModelSerializer):
    cells = serializers.SerializerMethodField()

    def get_cells(self, obj):
        if self.context.get("hide_cells", True):
            return None
        return PromptlySheetCellSeializer(obj.cells, many=True).data

    class Meta:
        model = PromptlySheet
        fields = ["uuid", "name", "extra_data", "cells", "created_at", "updated_at"]


class PromptlySheetCellSeializer(serializers.ModelSerializer):
    class Meta:
        model = PromptlySheetCell
        fields = ["row", "column", "value", "value_type", "display_value", "extra_data", "created_at", "updated_at"]
