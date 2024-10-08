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
    run_id = serializers.SerializerMethodField()
    scheduled_run_config = serializers.SerializerMethodField()

    def get_cells(self, obj):
        cells = {}
        if self.context.get("include_cells", False):
            for cell_id, cell in obj.cells.items():
                cells[cell_id] = cell.model_dump()

        return cells

    def get_columns(self, obj):
        return obj.data.get("columns", [])

    def get_description(self, obj):
        return obj.data.get("description", "")

    def get_total_rows(self, obj):
        return obj.data.get("total_rows", 0)

    def get_total_columns(self, obj):
        return obj.data.get("total_columns", 0)

    def get_running(self, obj):
        return obj.extra_data.get("running", False)

    def get_run_id(self, obj):
        return obj.extra_data.get("run_id", None)

    def get_scheduled_run_config(self, obj):
        return obj.extra_data.get("scheduled_run_config", None)

    class Meta:
        model = PromptlySheet
        fields = [
            "uuid",
            "name",
            "cells",
            "columns",
            "total_rows",
            "total_columns",
            "description",
            "created_at",
            "updated_at",
            "running",
            "run_id",
            "scheduled_run_config",
        ]
