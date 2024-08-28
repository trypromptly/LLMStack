import logging

from rest_framework import serializers

from llmstack.sheets.models import PromptlySheet

logger = logging.getLogger(__name__)


class PromptlySheetSerializer(serializers.ModelSerializer):
    cells = serializers.SerializerMethodField()
    columns = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    total_rows = serializers.SerializerMethodField()
    total_columns = serializers.SerializerMethodField()
    running = serializers.SerializerMethodField()

    def get_cells(self, obj):
        cells = {}
        if self.context.get("include_cells", False):
            for cell_id, cell in obj.cells.items():
                cells[cell_id] = cell.model_dump()

        return cells

    def get_columns(self, obj):
        return {col.col: col.model_dump() for col in obj.columns}

    def get_description(self, obj):
        return obj.data.get("description", "")

    def get_total_rows(self, obj):
        return obj.data.get("total_rows", 0)

    def get_total_columns(self, obj):
        return obj.data.get("total_columns", 0)

    def get_running(self, obj):
        return obj.extra_data.get("running", False)

    class Meta:
        model = PromptlySheet
        fields = [
            "uuid",
            "name",
            "extra_data",
            "cells",
            "columns",
            "total_rows",
            "total_columns",
            "description",
            "created_at",
            "updated_at",
            "running",
        ]
