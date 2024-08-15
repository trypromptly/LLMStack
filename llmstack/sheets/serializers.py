from rest_framework import serializers

from llmstack.sheets.models import PromptlySheet


class PromptlySheetSeializer(serializers.ModelSerializer):
    cells = serializers.SerializerMethodField()

    def get_cells(self, obj):
        cells = {}
        if self.context.get("include_cells", False):
            for page in obj.cells:
                for cell_row in page:
                    cells[str(cell_row)] = dict(map(lambda x: (str(x[0]), x[1].model_dump()), page[cell_row].items()))

        return cells

    class Meta:
        model = PromptlySheet
        fields = ["uuid", "name", "extra_data", "cells", "created_at", "updated_at"]
