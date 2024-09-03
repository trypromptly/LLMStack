import csv
import io
import logging
import uuid

from django.http import StreamingHttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response as DRFResponse
from rq import Callback

from llmstack.base.models import Profile
from llmstack.common.utils.sslr._client import LLM
from llmstack.jobs.adhoc import ProcessingJob
from llmstack.sheets.models import (
    PromptlySheet,
    PromptlySheetCell,
    PromptlySheetColumn,
    PromptlySheetFormulaCell,
    PromptlySheetRunEntry,
)
from llmstack.sheets.serializers import PromptlySheetSerializer
from llmstack.sheets.yaml_loader import load_sheet_templates

logger = logging.getLogger(__name__)


def _get_sheet_csv(columns, cells, total_rows):
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Write header
    writer.writerow([col.title for col in columns])
    yield output.getvalue()
    output.seek(0)
    output.truncate(0)

    for row in range(1, total_rows + 1):
        # Create a dict of cell_id to cell from this row
        row_cells = {cell.cell_id: cell for cell in cells.values() if cell.row == row}

        # Create a list of cell values for this row, using an empty string if the cell doesn't exist
        row_values = []
        for column in columns:
            cell = row_cells.get(f"{column.col}{row}")
            row_values.append(cell.data.get("output", "") if isinstance(cell.data, dict) else cell.data if cell else "")

        writer.writerow(row_values)
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)


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
        sheets = PromptlySheet.objects.filter(profile_uuid=profile.uuid).order_by("-updated_at")
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
            data={
                "description": request.data.get("description", ""),
                "columns": request.data.get("columns", {}),
                "formula_cells": request.data.get("formula_cells", {}),
                "total_rows": request.data.get("total_rows", 0),
                "total_columns": request.data.get("total_columns", 26),
            },
            extra_data=request.data.get("extra_data", {"has_header": True}),
        )

        if "cells" in request.data:
            cells = [PromptlySheetCell(**cell_data) for cell_data in request.data.get("cells", {}).values()]
            sheet.save(cells=cells, update_fields=["data"])

        return DRFResponse(PromptlySheetSerializer(instance=sheet).data)

    def delete(self, request, sheet_uuid=None):
        profile = Profile.objects.get(user=request.user)

        sheet = PromptlySheet.objects.get(uuid=sheet_uuid, profile_uuid=profile.uuid)

        # Delete associated PromptlySheetRunEntry entries
        PromptlySheetRunEntry.objects.filter(sheet_uuid=sheet.uuid).delete()

        sheet.delete()

        return DRFResponse(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, sheet_uuid=None):
        profile = Profile.objects.get(user=request.user)

        sheet = PromptlySheet.objects.get(uuid=sheet_uuid, profile_uuid=profile.uuid)
        sheet.name = request.data.get("name", sheet.name)
        sheet.extra_data = request.data.get("extra_data", sheet.extra_data)

        if "total_rows" in request.data:
            sheet.data["total_rows"] = request.data["total_rows"]

        if "total_columns" in request.data:
            sheet.data["total_columns"] = request.data["total_columns"]

        if "description" in request.data:
            sheet.data["description"] = request.data["description"]

        if "formula_cells" in request.data:
            sheet.data["formula_cells"] = {
                cell_id: PromptlySheetFormulaCell(**cell_data).model_dump()
                for cell_id, cell_data in request.data["formula_cells"].items()
            }

        if "columns" in request.data:
            sheet.data["columns"] = {
                column_data["col"]: PromptlySheetColumn(**column_data).model_dump()
                for column_data in request.data["columns"].values()
            }

        sheet.save()

        if "cells" in request.data:
            cell_objects = []
            for cell_id, cell_data in request.data.get("cells", {}).items():
                # Get the row and col from the cell_id
                row, col = PromptlySheetCell.cell_id_to_row_and_col(cell_id)
                cell_data["row"] = row
                cell_data["col"] = col

                cell_objects.append(cell_data)

            cells = [PromptlySheetCell(**cell_data) for cell_data in cell_objects]
            sheet.save(cells=cells, update_fields=["data"])

        return DRFResponse(PromptlySheetSerializer(instance=sheet).data)

    def run_async(self, request, sheet_uuid=None):
        profile = Profile.objects.get(user=request.user)
        sheet = PromptlySheet.objects.get(uuid=sheet_uuid, profile_uuid=profile.uuid)
        if sheet.is_locked:
            return DRFResponse(
                {"detail": "The sheet is locked and cannot be run at this time."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        run_entry = PromptlySheetRunEntry(sheet_uuid=sheet.uuid, profile_uuid=profile.uuid)

        job = PromptlySheetAppExecuteJob.create(
            func="llmstack.sheets.tasks.run_sheet",
            args=[sheet, run_entry, request.user],
            on_stopped=Callback("llmstack.sheets.tasks.on_sheet_run_stopped"),
            on_success=Callback("llmstack.sheets.tasks.on_sheet_run_success"),
            on_failure=Callback("llmstack.sheets.tasks.on_sheet_run_failed"),
        ).add_to_queue()

        # Add the job_id and run_id to the sheet
        sheet.is_locked = True
        sheet.extra_data["running"] = True
        sheet.extra_data["job_id"] = str(job.id)
        sheet.extra_data["run_id"] = str(run_entry.uuid)
        sheet.save(update_fields=["extra_data", "is_locked"])

        return DRFResponse({"job_id": job.id, "run_id": run_entry.uuid}, status=202)

    def cancel_run(self, request, sheet_uuid=None, run_id=None):
        profile = Profile.objects.get(user=request.user)
        sheet = PromptlySheet.objects.get(uuid=sheet_uuid, profile_uuid=profile.uuid)

        if not run_id:
            return DRFResponse(status=status.HTTP_400_BAD_REQUEST)

        run_id_in_sheet = sheet.extra_data.get("run_id")
        job_id = sheet.extra_data.get("job_id")

        if run_id_in_sheet != run_id:
            return DRFResponse(status=status.HTTP_400_BAD_REQUEST)
        PromptlySheetAppExecuteJob.cancel(job_id)

        sheet.extra_data["running"] = False
        sheet.extra_data["job_id"] = None
        sheet.extra_data["run_id"] = None
        sheet.is_locked = False
        sheet.save(update_fields=["extra_data", "is_locked"])

        return DRFResponse(status=status.HTTP_204_NO_CONTENT)

    def download(self, request, sheet_uuid=None):
        if not sheet_uuid:
            return DRFResponse(status=status.HTTP_400_BAD_REQUEST)

        profile = Profile.objects.get(user=request.user)

        sheet = PromptlySheet.objects.get(uuid=sheet_uuid, profile_uuid=profile.uuid)
        if not sheet:
            return DRFResponse(status=status.HTTP_404_NOT_FOUND)

        response = StreamingHttpResponse(
            streaming_content=_get_sheet_csv(sheet.columns, sheet.cells, sheet.data.get("total_rows", 0)),
            content_type="text/csv",
        )
        response["Content-Disposition"] = f'attachment; filename="sheet_{sheet_uuid}.csv"'
        return response

    def download_run(self, request, sheet_uuid=None, run_id=None):
        if not sheet_uuid or not run_id:
            return DRFResponse(status=status.HTTP_400_BAD_REQUEST)

        profile = Profile.objects.get(user=request.user)

        sheet = PromptlySheet.objects.get(uuid=sheet_uuid, profile_uuid=profile.uuid)
        run_entry = PromptlySheetRunEntry.objects.get(uuid=run_id, sheet_uuid=sheet.uuid)

        if not run_entry:
            return DRFResponse(status=status.HTTP_404_NOT_FOUND)

        response = StreamingHttpResponse(
            streaming_content=_get_sheet_csv(sheet.columns, sheet.cells, sheet.data.get("total_rows", 0)),
            content_type="text/csv",
        )
        response["Content-Disposition"] = f'attachment; filename="sheet_{sheet_uuid}_{run_id}.csv"'
        return response

    @action(detail=True, methods=["get"])
    def list_runs(self, request, sheet_uuid=None):
        profile = Profile.objects.get(user=request.user)
        sheet = PromptlySheet.objects.get(uuid=sheet_uuid, profile_uuid=profile.uuid)

        run_entries = PromptlySheetRunEntry.objects.filter(sheet_uuid=sheet.uuid).order_by("-created_at")

        return DRFResponse([{"uuid": entry.uuid, "created_at": entry.created_at} for entry in run_entries])

    @action(detail=True, methods=["post"])
    def generate_data_transformation_template(self, request):
        # Generate a liquidjs template for data transformation
        prompt = request.data.get("prompt")
        user = request.user
        profile = Profile.objects.get(user=user)

        if not prompt or not profile:
            return DRFResponse(status=status.HTTP_400_BAD_REQUEST)

        system_message = """You are an AI assistant that generates a liquidjs template for data transformation. You do not generate any text other than the template.
        """
        message = f"""- You have access to data with variables available as excel cells and columns. For example, A cell in row 1 column B can be referred as `B1`.
- When a column is directly referred as `B`, all the values of cells from that column will be available as a list in `B`.
- Similarly a range of cells from column B row 1 to column B row 10 can be referred as `B1-B10`. And a range of cells from column B row 1 to column C row 10 can be referred as `B1-C10`.
- Do not include any preamble or introduction. Do not include ```liquid or ```liquidjs
- Do not wrap the template in ```.
- Only include the template.
- Evaluating the template should return a single string or a list of strings or a list of lists of strings depending on the transformation you need to perform. When returning a list or a list of lists, use  to_json filter.
- Below are the list of valid filters that you can use. Do not include any other filters.
- Make sure the template can handle Nil values as they are not JSON serializable.
- You cannot use map on a sequence. For example, A1-A10 is a sequence and not a single value.

abs
append
at_least
at_most
base64_decode
base64_encode
base64_url_safe_decode
base64_url_safe_encode
capitalize
ceil
compact
concat
date
default
divided_by
downcase
escape
escape_once
escape_unicode
first
floor
join
last
lstrip
map
minus
modulo
newline_to_br
plus
prepend
remove
remove_first
remove_last
replace
replace_first
replace_last
reverse
round
rstrip
safe
size
slice
sort
sort_natural
split
strip
strip_html
strip_newlines
sum
times
to_dict
to_json
truncate
truncatewords
uniq
upcase
url_decode
url_encode
where

Now generate a liquidjs template for below instructions:

        {prompt}
        """

        model_slug = "gpt-4o-mini"
        provider_config = profile.get_provider_config(provider_slug="openai", processor_slug="*", model_slug=model_slug)
        if not provider_config:
            raise Exception(
                "OpenAI provider config not found. Please add a provider config for OpenAI to generate a template."
            )

        llm_client = LLM(
            provider="openai",
            openai_api_key=provider_config.api_key if provider_config else "",
        )

        result = llm_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": message},
            ],
            model=model_slug,
            max_tokens=1000,
            temperature=0.5,
            stream=False,
        )

        return DRFResponse({"template": result.choices[0].message.content})


class PromptlySheetTemplateViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list_templates(self, request, slug=None):
        templates = load_sheet_templates()
        if slug:
            return DRFResponse(templates.get(slug))

        return DRFResponse(templates)
