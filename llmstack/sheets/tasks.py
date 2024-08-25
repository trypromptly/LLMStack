import logging
import uuid
from typing import List

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.models import User
from django.test import RequestFactory
from rest_framework.response import Response as DRFResponse

from llmstack.common.utils.utils import hydrate_input
from llmstack.sheets.models import PromptlySheet, PromptlySheetCell, PromptlySheetColumn
from llmstack.sheets.serializers import PromptlySheetSerializer

try:
    from promptly.promptly_app_store.apis import AppStoreAppViewSet
except ImportError:
    from llmstack.app_store.apis import AppStoreAppViewSet


logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


def number_to_letters(num):
    letters = ""
    while num >= 0:
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[num % 26] + letters
        num = num // 26 - 1
    return letters


def _execute_cell(
    cell: PromptlySheetCell,
    column: PromptlySheetColumn,
    row: List[PromptlySheetCell],
    sheet: PromptlySheet,
    run_id: str,
    user: User,
) -> PromptlySheetCell:
    if column.kind != "app_run":
        return cell

    async_to_sync(channel_layer.group_send)(run_id, {"type": "cell.updating", "cell": {"id": cell.cell_id}})

    app_slug = column.data["app_slug"]
    input_values = {cell.col: cell.display_data for cell in row}
    input = hydrate_input(column.data["input"], input_values)

    request = RequestFactory().post(
        f"/api/store/apps/{app_slug}",
        format="json",
    )
    request.data = {
        "stream": False,
        "input": input,
    }
    request.user = user

    # Execute the app
    response = async_to_sync(AppStoreAppViewSet().run_app_internal_async)(
        slug=app_slug,
        session_id=None,
        request_uuid=str(uuid.uuid4()),
        request=request,
    )

    output = response.get("output", "")
    async_to_sync(channel_layer.group_send)(
        run_id, {"type": "cell.update", "cell": {"id": cell.cell_id, "data": response.get("output", "")}}
    )
    cell.display_data = output if isinstance(output, str) else str(output)

    return cell


def run_sheet(sheet, run_entry, user):
    try:
        processed_cells = []
        existing_cells_dict = sheet.cells
        existing_cells = list(existing_cells_dict.values())
        existing_cols = sheet.columns

        async_to_sync(channel_layer.group_send)(
            str(run_entry.uuid), {"type": "sheet.status", "sheet": {"id": str(sheet.uuid), "running": True}}
        )

        for row_number in range(1, sheet.data.get("total_rows", 0) + 1):
            for column in existing_cols:
                if column.kind != "app_run":
                    if f"{column.col}{row_number}" in existing_cells_dict:
                        processed_cells.append(existing_cells_dict[f"{column.col}{row_number}"])
                    continue

                # Create a new cell
                cell_to_execute = PromptlySheetCell(
                    row=row_number,
                    col=column.col,
                    kind=column.kind,
                )
                processed_cells.append(
                    _execute_cell(
                        cell_to_execute,
                        column,
                        list(filter(lambda cell: cell.row == row_number, existing_cells)),
                        sheet,
                        str(run_entry.uuid),
                        user,
                    )
                )

        if processed_cells:
            sheet.save(cells=processed_cells, update_fields=["updated_at"])
            # Store the processed data in sheet runs table
            run_entry.save(cells=processed_cells)

    except Exception:
        logger.exception("Error executing sheet")

    sheet.extra_data["running"] = False
    sheet.is_locked = False
    sheet.save(update_fields=["is_locked", "extra_data"])

    async_to_sync(channel_layer.group_send)(
        str(run_entry.uuid), {"type": "sheet.status", "sheet": {"id": str(sheet.uuid), "running": False}}
    )

    return DRFResponse(PromptlySheetSerializer(instance=sheet).data)
