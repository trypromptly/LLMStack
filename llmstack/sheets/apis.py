import logging
import uuid

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response as DRFResponse

from llmstack.base.models import Profile
from llmstack.jobs.adhoc import ProcessingJob
from llmstack.sheets.models import PromptlySheet, PromptlySheetCell
from llmstack.sheets.serializers import PromptlySheetSeializer
from llmstack.sheets.utils import parse_formula

logger = logging.getLogger(__name__)


def write_to_ws_channel(channel_name, message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.send)(channel_name, {"type": "send.message", "message": message})


class PromptlySheetAppExecuteJob(ProcessingJob):
    @classmethod
    def generate_job_id(cls):
        return "{}".format(str(uuid.uuid4()))


def _execute_cell(cell: PromptlySheetCell, sheet: PromptlySheet) -> PromptlySheetCell:
    if not cell.is_formula:
        return cell

    # Else execute the formula
    function_name, params = parse_formula(cell.value)
    if not function_name or not params:
        display_value = f"Invalid formula: {cell.value}"
    else:
        resolved_params = [""] * len(params)
        for param_index in range(len(params)):
            if "-" in params[param_index]:
                column, row = params[param_index].split("-")
                resolved_cell = sheet.get_cell(int(row), int(column))
                resolved_params[param_index] = resolved_cell.value

        display_value = f"Executing {function_name}({', '.join(resolved_params)})"

    extra_data = {**cell.extra_data}
    extra_data["display_value"] = display_value
    new_cell = cell.model_copy(update={"extra_data": extra_data})
    ws_channel_name = sheet.extra_data.get("channel_name")
    if ws_channel_name:
        write_to_ws_channel(ws_channel_name, new_cell.model_dump())

    return new_cell


class PromptlySheetViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request, sheet_uuid=None):
        profile = Profile.objects.get(user=request.user)
        include_cells = request.query_params.get("include_cells", "false").lower() == "true"

        if sheet_uuid:
            sheet = PromptlySheet.objects.get(uuid=sheet_uuid, profile_uuid=profile.uuid)
            return DRFResponse(
                PromptlySheetSeializer(
                    instance=sheet,
                    context={
                        "include_cells": include_cells,
                    },
                ).data
            )
        sheets = PromptlySheet.objects.filter(profile_uuid=profile.uuid)
        return DRFResponse(
            PromptlySheetSeializer(
                instance=sheets,
                many=True,
                context={
                    "include_cells": include_cells,
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
            if not isinstance(request.data["cells"], dict):
                raise ValueError("Invalid cells data")

            cells_data = {}
            for row_number in request.data["cells"]:
                row_cell_data = {}
                if not isinstance(request.data["cells"][row_number], dict):
                    raise ValueError("Invalid cells data")
                for column_number in request.data["cells"][row_number]:
                    cell_data = request.data["cells"][row_number][column_number]
                    row_cell_data[int(column_number)] = PromptlySheetCell(
                        row=row_number, col=column_number, **cell_data
                    )
                cells_data[int(row_number)] = row_cell_data

            sheet.save(cells=cells_data)

        return DRFResponse(PromptlySheetSeializer(instance=sheet).data)

    def delete(self, request, sheet_uuid=None):
        profile = Profile.objects.get(user=request.user)

        sheet = PromptlySheet.objects.get(uuid=sheet_uuid, profile_uuid=profile.uuid)
        sheet.delete()

        return DRFResponse(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, sheet_uuid=None):
        profile = Profile.objects.get(user=request.user)

        sheet = PromptlySheet.objects.get(uuid=sheet_uuid, profile_uuid=profile.uuid)
        sheet.name = request.data.get("name", sheet.name)
        sheet.extra_data = request.data.get("extra_data", sheet.extra_data)
        sheet.save()

        if "cells" in request.data:
            cells_data = []
            for row in range(len(request.data["cells"])):
                cells_row_data = []
                for column in range(len(request.data["cells"][row])):
                    cell_data = request.data["cells"][row][column]
                    cells_row_data.append(PromptlySheetCell(row=row, col=column, **cell_data))
                cells_data.append(cells_row_data)
            sheet.save(cells=cells_data)

        return DRFResponse(PromptlySheetSeializer(instance=sheet).data)

    def execute(self, request, sheet_uuid=None):
        profile = Profile.objects.get(user=request.user)

        sheet = PromptlySheet.objects.get(uuid=sheet_uuid, profile_uuid=profile.uuid)
        if sheet.is_locked:
            return DRFResponse(
                {"detail": "The sheet is locked and cannot be executed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sheet.is_locked = True
        sheet.save(update_fields=["is_locked"])

        try:
            processed_cells = []
            for row in sheet.rows:
                processed_cells_row = []
                for cell in row:
                    processed_cells_row.append(_execute_cell(cell, sheet))
                processed_cells.append(processed_cells_row)

            if processed_cells:
                sheet.save(cells=processed_cells, update_fields=["updated_at"])
        except Exception:
            logger.exception("Error executing sheet")

        sheet.is_locked = False
        sheet.save(update_fields=["is_locked"])
        return DRFResponse(PromptlySheetSeializer(instance=sheet).data)

    def execute_async(self, request, sheet_uuid=None):
        job = PromptlySheetAppExecuteJob.create(
            func="llmstack.promptly_sheets.tasks.process_sheet_execute_request",
            args=[request.user.email, sheet_uuid],
        ).add_to_queue()

        return DRFResponse({"job_id": job.id}, status=202)
