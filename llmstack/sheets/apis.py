import logging
import uuid

from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response as DRFResponse

from llmstack.base.models import Profile
from llmstack.jobs.adhoc import ProcessingJob
from llmstack.sheets.models import (
    PromptlySheet,
    PromptlySheetCell,
    PromptlySheetColumn,
    PromptlySheetRunEntry,
)
from llmstack.sheets.serializers import PromptlySheetSerializer

logger = logging.getLogger(__name__)


class PromptlySheetAppExecuteJob(ProcessingJob):
    @classmethod
    def generate_job_id(cls):
        return "{}".format(str(uuid.uuid4()))


class PromptlySheetViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request, sheet_uuid=None):
        profile = Profile.objects.get(user=request.user)
        include_cells = request.query_params.get("include_cells", "false").lower() == "true"

        if sheet_uuid:
            sheet = PromptlySheet.objects.get(uuid=sheet_uuid, profile_uuid=profile.uuid)
            return DRFResponse(
                PromptlySheetSerializer(
                    instance=sheet,
                    context={
                        "include_cells": include_cells,
                    },
                ).data
            )
        sheets = PromptlySheet.objects.filter(profile_uuid=profile.uuid)
        return DRFResponse(
            PromptlySheetSerializer(
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
            data=request.data.get("data", {}),
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

        return DRFResponse(PromptlySheetSerializer(instance=sheet).data)

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

        if "data" in request.data:
            if "columns" in request.data["data"]:
                sheet.data["columns"] = [
                    PromptlySheetColumn(**column_data).model_dump() for column_data in request.data["data"]["columns"]
                ]

            if "total_rows" in request.data["data"]:
                sheet.data["total_rows"] = request.data["data"]["total_rows"]

            if "description" in request.data["data"]:
                sheet.data["description"] = request.data["data"]["description"]

        sheet.save()

        if "data" in request.data and "cells" in request.data["data"]:
            cells_data = []
            for row_number in request.data["data"]["cells"]:
                if not isinstance(request.data["data"]["cells"][row_number], dict):
                    raise ValueError("Invalid cells data")
                for column_number in request.data["data"]["cells"][row_number]:
                    cell_data = request.data["data"]["cells"][row_number][column_number]
                    cell_data.pop("row", None)
                    cell_data.pop("col", None)
                    cells_data.append(PromptlySheetCell(row=row_number, col=column_number, **cell_data))
            sheet.save(cells=cells_data)

        return DRFResponse(PromptlySheetSerializer(instance=sheet).data)

    def run_async(self, request, sheet_uuid=None):
        profile = Profile.objects.get(user=request.user)
        sheet = PromptlySheet.objects.get(uuid=sheet_uuid, profile_uuid=profile.uuid)
        if sheet.is_locked:
            return DRFResponse(
                {"detail": "The sheet is locked and cannot be run at this time."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sheet.is_locked = True
        sheet.save(update_fields=["is_locked"])

        run_entry = PromptlySheetRunEntry(sheet_uuid=sheet.uuid, profile_uuid=profile.uuid)

        job = PromptlySheetAppExecuteJob.create(
            func="llmstack.sheets.tasks.run_sheet",
            args=[sheet, run_entry, request.user],
        ).add_to_queue()

        return DRFResponse({"job_id": job.id, "run_id": run_entry.uuid}, status=202)
