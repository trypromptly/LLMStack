import logging
import uuid

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
    row: dict[str, PromptlySheetCell],
    sheet: PromptlySheet,
    run_id: str,
    user: User,
) -> PromptlySheetCell:
    if column.kind != "app_run":
        return cell

    async_to_sync(channel_layer.group_send)(run_id, {"type": "cell.updating", "cell": {"id": cell.cell_id}})

    app_slug = column.data["app_slug"]
    input_values = {number_to_letters(col): cell.data for col, cell in row.items()}
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
    cell.data = output

    return cell


def run_sheet(sheet, run_entry, user):
    try:
        processed_cells = []
        existing_rows = list(sheet.rows)
        existing_cols = sheet.columns

        for row_number in range(sheet.data.get("total_rows", 0)):
            # Find existing row and the cell
            existing_row = next(filter(lambda row: row[0] == row_number, existing_rows), None)
            existing_row_cells = existing_row[1] if existing_row else {}

            for column in existing_cols:
                if column.kind != "app_run":
                    if existing_row:
                        existing_cell = next(
                            filter(lambda cell: cell.col == column.col, existing_row_cells.values()), None
                        )
                        if existing_cell:
                            processed_cells.append(existing_cell)
                    continue

                # Create a new cell
                cell_to_execute = PromptlySheetCell(
                    row=row_number,
                    col=column.col,
                    kind=column.kind,
                )
                processed_cells.append(
                    _execute_cell(cell_to_execute, column, existing_row_cells, sheet, str(run_entry.uuid), user)
                )

        if processed_cells:
            sheet.save(cells=processed_cells, update_fields=["updated_at"])
            # Store the processed data in sheet runs table
            run_entry.save(cells=processed_cells)

    except Exception:
        logger.exception("Error executing sheet")

    sheet.is_locked = False
    sheet.save(update_fields=["is_locked"])
    return DRFResponse(PromptlySheetSerializer(instance=sheet).data)
