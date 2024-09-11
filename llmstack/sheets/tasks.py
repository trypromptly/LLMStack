import ast
import concurrent
import json
import logging
import re
import uuid
from threading import Lock
from typing import Any, Dict, List

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.models import User
from django.test import RequestFactory
from django_redis import get_redis_connection
from jsonpath_ng import parse

from llmstack.apps.apis import AppViewSet
from llmstack.common.utils.liquid import render_template
from llmstack.common.utils.utils import hydrate_input
from llmstack.sheets.models import (
    PromptlySheet,
    PromptlySheetRunEntry,
    SheetCell,
    SheetCellType,
    SheetColumn,
    SheetFormulaType,
)

try:
    from promptly_app_store.apis import AppStoreAppViewSet
except ImportError:
    from llmstack.app_store.apis import AppStoreAppViewSet


logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()
sheet_run_data_store = get_redis_connection("sheet_run_data_store")

# Add a global lock for thread-safe operations
global_lock = Lock()


def number_to_letters(num):
    letters = ""
    while num >= 0:
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[num % 26] + letters
        num = num // 26 - 1
    return letters


def _execute_cell(
    cell: SheetCell,
    cell_type: SheetCellType,
    input_values: Dict[str, Any],
    sheet: PromptlySheet,
    run_id: str,
    user: User,
) -> List[SheetCell]:
    if not cell.formula:
        return [cell]

    async_to_sync(channel_layer.group_send)(run_id, {"type": "cell.updating", "cell": {"id": cell.cell_id}})

    output = None
    output_cells = []
    formula_type = cell.formula.type
    formula_data = cell.formula.data
    spread_output = cell.spread_output

    if formula_type == SheetFormulaType.APP_RUN:
        app_slug = formula_data.app_slug
        input = hydrate_input(formula_data.input, input_values)

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
    elif formula_type == SheetFormulaType.PROCESSOR_RUN:
        api_provider_slug = formula_data.provider_slug
        api_backend_slug = formula_data.processor_slug
        processor_input = formula_data.input
        processor_config = formula_data.config
        processor_output_template = formula_data.output_template.get("jsonpath", "")

        input = hydrate_input(processor_input, input_values)
        config = hydrate_input(processor_config, input_values)

        request = RequestFactory().post(
            f"/api/playground/{api_provider_slug}_{api_backend_slug}/run",
            format="json",
        )
        request.data = {
            "stream": False,
            "input": {
                "input": input,
                "config": config,
                "api_provider_slug": api_provider_slug,
                "api_backend_slug": api_backend_slug,
            },
        }
        request.user = user

        # Run the processor
        response = async_to_sync(AppViewSet().run_playground_internal_async)(
            session_id=None,
            request_uuid=str(uuid.uuid4()),
            request=request,
            preview=False,
        )

        # Render the output template using response.output
        if response.get("output"):
            try:
                processor_output = ast.literal_eval(response.get("output"))
                jsonpath_output = [match.value for match in parse(processor_output_template).find(processor_output)]
                if len(jsonpath_output) == 1:
                    jsonpath_output = jsonpath_output[0]

                output = jsonpath_output if cell_type == SheetCellType.OBJECT else str(jsonpath_output)

            except Exception as e:
                logger.error(f"Error processing processor output: {e}")
                async_to_sync(channel_layer.group_send)(
                    run_id, {"type": "cell.error", "cell": {"id": cell.cell_id, "error": str(e)}}
                )
                output = ""
        else:
            output = response.get("output", "")
    elif formula_type == SheetFormulaType.DATA_TRANSFORMER:
        transformation_template = formula_data.transformation_template
        if transformation_template:
            try:
                output = render_template(transformation_template, input_values)
            except Exception as e:
                logger.error(f"Error applying transformation template: {e}")
                async_to_sync(channel_layer.group_send)(
                    run_id, {"type": "cell.error", "cell": {"id": cell.cell_id, "error": str(e)}}
                )
        else:
            output = ""
    try:
        processed_output = output if cell_type == SheetCellType.OBJECT else ast.literal_eval(output)

        if (
            isinstance(processed_output, list)
            and cell.spread_output
            and all(isinstance(item, list) for item in processed_output)
        ):
            output_cells = [
                SheetCell(
                    row=cell.row + i,
                    col_letter=SheetColumn.column_index_to_letter(
                        SheetColumn.column_letter_to_index(cell.col_letter) + j
                    ),
                    value=str(item),
                )
                for i, row in enumerate(processed_output)
                for j, item in enumerate(row)
            ]
        elif isinstance(processed_output, list) and spread_output:
            output_cells = [
                SheetCell(
                    row=cell.row + i,
                    col_letter=cell.col_letter,
                    value=item if cell_type == SheetCellType.OBJECT else str(item),
                )
                for i, item in enumerate(processed_output)
            ]
        else:
            cell.value = str(processed_output if isinstance(processed_output, str) else output)
            output_cells = [cell]
    except Exception as e:
        logger.error(f"Error processing cell: {e}")
        cell.value = str(output)
        output_cells = [cell]

    total_rows = sheet.data.get("total_rows", 0)
    total_cols = sheet.data.get("total_cols", 0)
    max_row_in_results = max(total_rows, max(cell.row for cell in output_cells))
    max_col_in_results = max(
        total_cols,
        max(SheetColumn.column_letter_to_index(cell.col_letter) + 1 for cell in output_cells),
    )

    if max_row_in_results > total_rows or max_col_in_results > total_cols:
        async_to_sync(channel_layer.group_send)(
            str(run_id),
            {
                "type": "sheet.update",
                "sheet": {
                    "id": str(sheet.uuid),
                    "total_rows": max_row_in_results,
                    "total_cols": max_col_in_results,
                },
            },
        )

    for output_cell in output_cells:
        async_to_sync(channel_layer.group_send)(
            str(run_id),
            {
                "type": "cell.update",
                "cell": {
                    "id": output_cell.cell_id,
                    "value": output_cell.value,
                },
            },
        )

    return output_cells


def process_cell_references(data, existing_cells_dict, input_values=None):
    if input_values is None:
        input_values = {}

    if isinstance(data, dict):
        for value in data.values():
            process_cell_references(value, existing_cells_dict, input_values)
    elif isinstance(data, list):
        for item in data:
            process_cell_references(item, existing_cells_dict, input_values)
    elif isinstance(data, str):
        cell_refs = re.findall(r"([A-Z]+\d+(?:-[A-Z]+\d+)?)", data)
        for ref in cell_refs:
            if "-" in ref:
                start, end = ref.split("-")
                start_row, start_col = SheetCell.cell_id_to_row_and_col(start)
                end_row, end_col = SheetCell.cell_id_to_row_and_col(end)
                range_values = [
                    existing_cells_dict[f"{SheetColumn.column_index_to_letter(col)}{row}"].value
                    for row in range(start_row, end_row + 1)
                    for col in range(
                        SheetColumn.column_letter_to_index(start_col), SheetColumn.column_letter_to_index(end_col) + 1
                    )
                    if f"{SheetColumn.column_index_to_letter(col)}{row}" in existing_cells_dict
                ]
                input_values[ref] = range_values
            elif ref in existing_cells_dict:
                input_values[ref] = existing_cells_dict[ref].value

    return input_values


def create_subsheets(formula_cells_dict, total_cols):
    formula_columns = sorted(
        set(SheetColumn.column_letter_to_index(cell.col_letter) for cell in formula_cells_dict.values())
    )
    subsheets = []
    start = 0
    for col in formula_columns:
        if start < col:
            subsheets.append((start, col - 1))
        subsheets.append((col, col))
        start = col + 1
    if start < total_cols:
        subsheets.append((start, total_cols - 1))
    return subsheets


def column_in_selected_grid(selected_grid, column):
    for cell_range in selected_grid:
        if "-" in cell_range:
            start, end = cell_range.split("-")
            start_row, start_col = SheetCell.cell_id_to_row_and_col(start)
            end_row, end_col = SheetCell.cell_id_to_row_and_col(end)
            if SheetColumn.column_letter_to_index(start_col) <= column <= SheetColumn.column_letter_to_index(end_col):
                return True
        else:
            row, col = SheetCell.cell_id_to_row_and_col(cell_range)
            if SheetColumn.column_letter_to_index(col) == column:
                return True
    return False


def cell_in_selected_grid(selected_grid, cell):
    for cell_range in selected_grid:
        if "-" in cell_range:
            start, end = cell_range.split("-")
            start_row, start_col = SheetCell.cell_id_to_row_and_col(start)
            end_row, end_col = SheetCell.cell_id_to_row_and_col(end)
            if (
                SheetColumn.column_letter_to_index(start_col)
                <= SheetColumn.column_letter_to_index(cell.col_letter)
                <= SheetColumn.column_letter_to_index(end_col)
                and start_row <= cell.row <= end_row
            ):
                return True
        else:
            cell_row, cell_col = SheetCell.cell_id_to_row_and_col(cell_range)
            if cell_col == cell.col_letter and cell_row == cell.row:
                return True
    return False


def run_row(
    current_row,
    subsheet_start,
    subsheet_end,
    existing_cells_dict,
    columns_dict,
    formula_cells_dict,
    sheet,
    run_entry,
    user,
    valid_cells_in_row_from_prev_cols,
    selected_grid,
):
    valid_cells_in_row = valid_cells_in_row_from_prev_cols.copy()
    executed_cells = []
    for current_col_index in range(subsheet_start, subsheet_end + 1):
        current_col = SheetColumn.column_index_to_letter(current_col_index)
        current_cell_id = f"{current_col}{current_row}"
        previous_cell_id = f"{SheetColumn.column_index_to_letter(current_col_index)}{current_row}"

        if (
            previous_cell_id in existing_cells_dict
            and existing_cells_dict[previous_cell_id].value
            and existing_cells_dict[previous_cell_id].value != ""
        ):
            valid_cells_in_row.append(existing_cells_dict.get(previous_cell_id))

        # If selected_grid is provided and the cell is not in the selected grid, we don't need to execute it
        if selected_grid and not cell_in_selected_grid(
            selected_grid, SheetCell(row=current_row, col_letter=current_col)
        ):
            if current_cell_id in existing_cells_dict:
                valid_cells_in_row.append(existing_cells_dict.get(current_cell_id))
            continue

        if current_cell_id in formula_cells_dict:
            input_values = process_cell_references(
                formula_cells_dict[current_cell_id].formula.data, existing_cells_dict
            )

            # For formula cells, we pass entire columns data as input values
            for col in columns_dict.values():
                if SheetColumn.column_letter_to_index(col.col_letter) != current_col_index:
                    input_values[col.col_letter] = [
                        cell.value for cell in existing_cells_dict.values() if cell.col_letter == col.col_letter
                    ]

            executed_cells.extend(
                _execute_cell(
                    formula_cells_dict[current_cell_id],
                    columns_dict[current_col].cell_type,
                    input_values,
                    sheet,
                    str(run_entry.uuid),
                    user,
                )
            )
        elif (
            current_col in columns_dict
            and columns_dict[current_col].formula
            and columns_dict[current_col].formula.type != SheetFormulaType.NONE
            and valid_cells_in_row
        ):
            input_values = process_cell_references(columns_dict[current_col].formula.data, existing_cells_dict)

            for cell in valid_cells_in_row:
                input_values[cell.col_letter] = cell.value

            cell_to_execute = SheetCell(
                row=current_row,
                col_letter=current_col,
                value=columns_dict[current_col].formula.data,
                formula=columns_dict[current_col].formula,
                spread_output=False,
            )

            output_cells = _execute_cell(
                cell_to_execute,
                columns_dict[current_col].cell_type,
                input_values,
                sheet,
                str(run_entry.uuid),
                user,
            )

            executed_cells.extend(output_cells)

            # Update valid cells in row
            valid_cells_in_row.extend(output_cells)

    return executed_cells


def scheduled_run_sheet(sheet_uuid, user_id):
    sheet = PromptlySheet.objects.get(uuid=sheet_uuid)
    if sheet.is_locked:
        return "Sheet is locked"

    run_entry = PromptlySheetRunEntry(sheet_uuid=sheet.uuid, profile_uuid=sheet.profile_uuid)
    run_entry.save()

    return run_sheet(sheet_uuid, str(run_entry.uuid), user_id)


def run_sheet(
    sheet_uuid,
    run_entry_uuid,
    user_id,
    selected_grid=None,
    parallel_rows=4,
):
    try:
        sheet = PromptlySheet.objects.get(uuid=sheet_uuid)
        run_entry = PromptlySheetRunEntry.objects.get(uuid=run_entry_uuid)
        user = User.objects.get(id=user_id)

        existing_cells_dict = sheet.cells
        columns_dict = {col.col_letter: col for col in sheet.columns}
        formula_cells_dict = {cell.cell_id: cell for cell in sheet.cells.values() if cell.is_formula}
        formula_cell_columns = set(
            [SheetColumn.column_letter_to_index(cell.col_letter) for cell in formula_cells_dict.values()]
        )
        total_rows = sheet.data.get("total_rows", 0)
        total_cols = max((SheetColumn.column_letter_to_index(col.col_letter) for col in sheet.columns), default=0)

        async_to_sync(channel_layer.group_send)(
            str(run_entry.uuid),
            {
                "type": "sheet.status",
                "sheet": {"id": str(sheet.uuid), "running": True},
            },
        )

        subsheets = create_subsheets(formula_cells_dict, total_cols)

        max_iterations = 100  # Prevent infinite loop
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            sheet_grid_changed = False

            for subsheet_start, subsheet_end in subsheets:
                valid_cells_in_row_from_prev_cols = []
                row_step = (
                    1 if subsheet_start == subsheet_end and subsheet_start in formula_cell_columns else parallel_rows
                )

                for current_row in range(1, total_rows + 1, row_step):
                    executed_cells = []

                    # Prepare arguments for parallel execution
                    parallel_args = []
                    for row_index in range(current_row, min(current_row + row_step, total_rows + 1)):
                        valid_cells_in_row_from_prev_cols = [
                            cell
                            for cell in existing_cells_dict.values()
                            if cell.row == row_index
                            and SheetColumn.column_letter_to_index(cell.col_letter) < subsheet_start
                            and cell.value
                        ]

                        parallel_args.append(
                            (
                                row_index,
                                subsheet_start,
                                subsheet_end,
                                existing_cells_dict,
                                columns_dict,
                                formula_cells_dict,
                                sheet,
                                run_entry,
                                user,
                                valid_cells_in_row_from_prev_cols,
                                selected_grid,
                            )
                        )

                    # Execute run_row in parallel
                    with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(parallel_args))) as executor:
                        results = list(executor.map(lambda args: run_row(*args), parallel_args))

                    # Collect results
                    for result in results:
                        if result:
                            executed_cells.extend(result)

                    # Update the executed cells
                    with global_lock:
                        for cell in executed_cells:
                            existing_cells_dict[f"{cell.col_letter}{cell.row}"] = cell

                    # Update total rows and cols if the executed cells are beyond the current grid
                    if executed_cells:
                        max_row_in_executed_cells = max(cell.row for cell in executed_cells)
                        max_col_in_executed_cells = max(
                            SheetColumn.column_letter_to_index(cell.col_letter) for cell in executed_cells
                        )
                        if total_rows < max_row_in_executed_cells:
                            total_rows = max_row_in_executed_cells
                            sheet_grid_changed = True

                        if total_cols < max_col_in_executed_cells:
                            total_cols = max_col_in_executed_cells + 1
                            sheet_grid_changed = True

            if not sheet_grid_changed:
                break

            # Recompute subsheets if the grid changed
            subsheets = create_subsheets(formula_cells_dict, total_cols)

        if iteration == max_iterations:
            logger.warning("Maximum iterations reached. The sheet might not have fully converged.")

    except Exception as e:
        logger.exception("Error executing sheet")
        async_to_sync(channel_layer.group_send)(
            str(run_entry.uuid),
            {
                "type": "sheet.error",
                "error": f"Error executing sheet: {str(e)}",
            },
        )
        return False

    return True


def update_sheet_with_post_run_data(sheet_uuid, run_uuid):
    sheet = PromptlySheet.objects.get(uuid=sheet_uuid)

    sheet.is_locked = False
    sheet.extra_data["running"] = False
    sheet.extra_data["job_id"] = None
    sheet.extra_data["run_id"] = None

    run_entry = PromptlySheetRunEntry.objects.get(uuid=run_uuid)
    total_rows = sheet.data.get("total_rows", 0)
    total_cols = sheet.data.get("total_cols", 0)
    cells = sheet.cells

    # Process events in batches to avoid memory issues
    batch_size = 1000
    start = 0
    while True:
        events = sheet_run_data_store.lrange(run_uuid, start, start + batch_size - 1)
        if not events:
            break

        for event in events:
            try:
                event = json.loads(event)
            except json.JSONDecodeError:
                logger.error(f"Error parsing event: {event}")
                continue

            if event["type"] == "cell.update":
                cell_id = event["cell"]["id"]
                (row, col_letter) = SheetCell.cell_id_to_row_and_col(cell_id)
                cells[cell_id] = SheetCell(
                    row=row,
                    col_letter=col_letter,
                    value=event["cell"]["value"],
                    formula=cells[cell_id].formula if cell_id in cells else None,
                    spread_output=cells[cell_id].spread_output if cell_id in cells else False,
                )

            if event["type"] == "sheet.update":
                total_rows = max(total_rows, event["sheet"]["total_rows"])
                total_cols = max(total_cols, event["sheet"]["total_cols"])

        start += batch_size

    sheet.data["total_rows"] = total_rows
    sheet.data["total_cols"] = total_cols
    sheet.save(cells=cells.values(), update_fields=["data", "updated_at", "extra_data", "is_locked"])

    run_entry.data["total_rows"] = total_rows
    run_entry.data["total_cols"] = total_cols
    run_entry.save(cells=cells.values(), update_fields=["data"])

    # Delete the run data from redis
    sheet_run_data_store.delete(run_uuid)


def on_sheet_run_success(job, connection, result, *args, **kwargs):
    sheet_uuid = job.args[0]
    run_uuid = job.args[1]

    async_to_sync(channel_layer.group_send)(
        run_uuid,
        {
            "type": "sheet.status",
            "sheet": {"id": sheet_uuid, "running": False},
        },
    )

    update_sheet_with_post_run_data(sheet_uuid, run_uuid)


def on_sheet_run_failed(job, connection, type, value, traceback):
    sheet_uuid = job.args[0]
    run_uuid = job.args[1]

    async_to_sync(channel_layer.group_send)(
        run_uuid, {"type": "sheet.error", "error": f"Sheet run failed: {str(type)} - {str(value)}"}
    )

    update_sheet_with_post_run_data(sheet_uuid, run_uuid)


def on_sheet_run_stopped(job, connection):
    run_uuid = job.args[1]
    sheet_uuid = job.args[0]

    async_to_sync(channel_layer.group_send)(run_uuid, {"type": "sheet.disconnect", "reason": "Cancelled by user"})

    update_sheet_with_post_run_data(sheet_uuid, run_uuid)
