from rest_framework import serializers

from llmstack.promptly_sheets.models import PromptlySheet


class PromptlySheetSeializer(serializers.ModelSerializer):
    cells = serializers.SerializerMethodField()

    def get_cells(self, obj):
        cells = []
        if self.context.get("include_cells", False):
            for cells_page in obj.cells:
                for cells_row in cells_page:
                    cells.append([cell.model_dump() for cell in cells_row])
        return cells

    class Meta:
        model = PromptlySheet
        fields = ["uuid", "name", "extra_data", "cells", "created_at", "updated_at"]
