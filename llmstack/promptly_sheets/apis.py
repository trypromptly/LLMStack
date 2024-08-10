import logging

from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response as DRFResponse

from llmstack.base.models import Profile
from llmstack.promptly_sheets.models import PromptlySheet, PromptlySheetCell
from llmstack.promptly_sheets.serializers import (
    PromptlySheetCellSeializer,
    PromptlySheetSeializer,
)
from llmstack.promptly_sheets.utils import parse_formula

logger = logging.getLogger(__name__)


class PromptlySheetViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request, sheet_uuid=None):
        profile = Profile.objects.get(user=request.user)
        hide_cells = request.query_params.get("hide_cells", "true").lower() == "true"

        if sheet_uuid:
            sheet = PromptlySheet.objects.get(uuid=sheet_uuid, profile_uuid=profile.uuid)
            return DRFResponse(
                PromptlySheetSeializer(
                    instance=sheet,
                    context={
                        "hide_cells": hide_cells,
                    },
                ).data
            )
        sheets = PromptlySheet.objects.filter(profile_uuid=profile.uuid)
        return DRFResponse(
            PromptlySheetSeializer(
                instance=sheets,
                many=True,
                context={
                    "hide_cells": hide_cells,
                },
            ).data
        )

    def create(self, request):
        profile = Profile.objects.get(user=request.user)

        sheet = PromptlySheet.objects.create(
            name=request.data.get("name"),
            profile_uuid=profile.uuid,
            extra_data=request.data.get("extra_data", {"has_header": True}),
        )
        if "cells" in request.data:
            for row_number in range(len(request.data["cells"])):
                for column_number in range(len(request.data["cells"][row_number])):
                    cell_data = request.data["cells"][row_number][column_number]
                    PromptlySheetCellViewSet()._internal_upsert(sheet, row_number, column_number, cell_data)

        return DRFResponse(PromptlySheetSeializer(instance=sheet).data)

    def delete(self, request, sheet_uuid=None):
        profile = Profile.objects.get(user=request.user)

        sheet = PromptlySheet.objects.get(uuid=sheet_uuid, profile_uuid=profile.uuid)
        PromptlySheetCellViewSet().delete(request, sheet_uuid=sheet_uuid)
        sheet.delete()

        return DRFResponse(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, sheet_uuid=None):
        profile = Profile.objects.get(user=request.user)

        sheet = PromptlySheet.objects.get(uuid=sheet_uuid, profile_uuid=profile.uuid)
        sheet.name = request.data.get("name", sheet.name)
        sheet.extra_data = request.data.get("extra_data", sheet.extra_data)
        sheet.save()

        if "cells" in request.data:
            for row_number in range(len(request.data["cells"])):
                for column_number in range(len(request.data["cells"][row_number])):
                    cell_data = request.data["cells"][row_number][column_number]
                    PromptlySheetCellViewSet()._internal_upsert(sheet, row_number, column_number, cell_data)

        return DRFResponse(PromptlySheetSeializer(instance=sheet).data)

    def execute(self, request, sheet_uuid=None):
        profile = Profile.objects.get(user=request.user)

        sheet = PromptlySheet.objects.get(uuid=sheet_uuid, profile_uuid=profile.uuid)
        PromptlySheetCellViewSet()._internal_execute(sheet, None, None)
        sheet.save(update_fields=["updated_at"])
        return DRFResponse(PromptlySheetSeializer(instance=sheet).data)


class PromptlySheetCellViewSet(viewsets.ViewSet):
    authentication_classes = [IsAuthenticated]

    def list(self, request, sheet_uuid=None, row=None, column=None):
        profile = Profile.objects.get(user=request.user)

        sheet = PromptlySheet.objects.get(uuid=sheet_uuid, profile_uuid=profile.uuid)
        if row and column:
            cell = PromptlySheetCell.objects.get(sheet=sheet, row=row, column=column)
            return DRFResponse(PromptlySheetCellSeializer(instance=cell).data)

        cells = PromptlySheetCell.objects.filter(sheet=sheet)
        return DRFResponse(PromptlySheetCellSeializer(instance=cells, many=True).data)

    def _internal_upsert(self, sheet, row, column, request_data):
        PromptlySheetCell.objects.update_or_create(
            sheet=sheet,
            row=row,
            column=column,
            value=request_data.get("value", ""),
            value_type=request_data.get("value_type", "string"),
            extra_data=request_data.get("extra_data", {}),
        )

    def upsert(self, request, sheet_uuid=None, row=None, column=None):
        profile = Profile.objects.get(user=request.user)

        sheet = PromptlySheet.objects.get(uuid=sheet_uuid, profile_uuid=profile.uuid)
        self._internal_upsert(sheet, row, column, request.data)
        cell = PromptlySheetCell.objects.get(sheet=sheet, row=row, column=column)

        return DRFResponse(PromptlySheetCellSeializer(instance=cell).data)

    def delete(self, request, sheet_uuid=None, row=None, column=None):
        profile = Profile.objects.get(user=request.user)

        sheet = PromptlySheet.objects.get(uuid=sheet_uuid, profile_uuid=profile.uuid)
        if row and column:
            cell = PromptlySheetCell.objects.get(sheet=sheet, row=row, column=column)
            cell.delete()
        else:
            PromptlySheetCell.objects.filter(sheet=sheet).delete()

        return DRFResponse(status=status.HTTP_204_NO_CONTENT)

    def _execute_cell(self, cell):
        if not cell.is_formula:
            return PromptlySheetCellSeializer(instance=cell).data

        # Else execute the formula
        function_name, params = parse_formula(cell.value)
        if not function_name or not params:
            display_value = f"Invalid formula: {cell.value}"
        else:
            resolved_params = [""] * len(params)
            for param_index in range(len(params)):
                if "-" in params[param_index]:
                    column, row = params[param_index].split("-")
                    current_cell = PromptlySheetCell.objects.get(sheet=cell.sheet, row=row, column=column)
                    resolved_params[param_index] = current_cell.value

            display_value = f"Executing {function_name}({', '.join(resolved_params)})"

        cell.extra_data["display_value"] = display_value
        cell.save(update_fields=["extra_data", "updated_at"])
        return PromptlySheetCellSeializer(instance=cell).data

    def _internal_execute(self, sheet, row, column):
        result = []
        if row and column:
            cell = PromptlySheetCell.objects.get(sheet=sheet, row=row, column=column)
            result = self._execute_cell(cell)
        else:
            cells = PromptlySheetCell.objects.filter(sheet=sheet)
            for cell in cells:
                result.append(self._execute_cell(cell))

        return result

    def execute(self, request, sheet_uuid=None, row=None, column=None):
        profile = Profile.objects.get(user=request.user).uuid
        sheet = PromptlySheet.objects.get(uuid=sheet_uuid, profile_uuid=profile.uuid)
        cells = PromptlySheetCellViewSet()._internal_execute(sheet, row, column)

        return DRFResponse(cells)
