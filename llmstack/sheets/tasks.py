import ast
import logging
import re
import uuid
from typing import Any, Dict, List, Optional

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.models import User
from django.test import RequestFactory
from rest_framework.response import Response as DRFResponse

from llmstack.apps.apis import AppViewSet
from llmstack.common.utils.liquid import render_template
from llmstack.common.utils.utils import hydrate_input
from llmstack.sheets.models import (
    PromptlySheet,
    PromptlySheetCell,
    PromptlySheetColumn,
    PromptlySheetColumnType,
    PromptlySheetFormulaCell,
)
from llmstack.sheets.serializers import PromptlySheetSerializer

try:
    from promptly_app_store.apis import AppStoreAppViewSet
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
    column: Optional[PromptlySheetColumn],
    input_values: Dict[str, Any],
    sheet: PromptlySheet,
    run_id: str,
    user: User,
) -> List[PromptlySheetCell]:
    is_formula_cell = isinstance(cell, PromptlySheetFormulaCell)
    if not is_formula_cell and column.type not in ["app_run", "processor_run", "data_transformer"]:
        return [cell]

    async_to_sync(channel_layer.group_send)(run_id, {"type": "cell.updating", "cell": {"id": cell.cell_id}})

    output = None
    output_cells = []
    execution_type = column.type if not is_formula_cell else cell.formula.type
    execution_data = column.data if not is_formula_cell else cell.formula.data

    if execution_type == "app_run":
        app_slug = execution_data["app_slug"]
        input = hydrate_input(execution_data["input"], input_values)

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
    elif execution_type == "processor_run":
        api_provider_slug = execution_data["provider_slug"]
        api_backend_slug = execution_data["processor_slug"]
        processor_input = execution_data.get("input", {})
        processor_config = execution_data.get("config", {})
        processor_output_template = execution_data.get("output_template", {}).get("markdown", "")

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
        if response.get("output") and processor_output_template:
            try:
                processor_output = ast.literal_eval(response.get("output"))
                output = hydrate_input(processor_output_template, processor_output)
            except Exception as e:
                logger.error(f"Error rendering output template: {e}")
                output = ""
        else:
            output = response.get("output", "")
    elif execution_type == "data_transformer":
        transformation_template = execution_data.get("transformation_template")
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

    if is_formula_cell:
        try:
            processed_output = ast.literal_eval(output)
            if isinstance(processed_output, list) and cell.spread_output:
                output_cells = [
                    PromptlySheetCell(
                        row=cell.row + i,
                        col=cell.col,
                        data={"output": str(item)},
                    )
                    for i, item in enumerate(processed_output)
                ]
            elif isinstance(processed_output, str) and cell.spread_output:
                output_cells = [
                    PromptlySheetCell(
                        row=cell.row,
                        col=cell.col,
                        data={"output": str(processed_output)},
                    )
                ]
            elif (
                isinstance(processed_output, list)
                and cell.spread_output
                and all(isinstance(item, list) for item in processed_output)
            ):
                output_cells = [
                    PromptlySheetCell(
                        row=cell.row + i,
                        col=PromptlySheetColumn.column_index_to_letter(
                            PromptlySheetColumn.column_letter_to_index(cell.col) + j
                        ),
                        data={"output": str(item)},
                    )
                    for i, row in enumerate(processed_output)
                    for j, item in enumerate(row)
                ]
            else:
                cell.data = {"output": str(output)}
                output_cells = [cell]
        except Exception:
            cell.data = {"output": str(output)}
            output_cells = [cell]
    else:
        cell.data = {"output": output}
        output_cells = [cell]

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
                start_row, start_col = PromptlySheetCell.cell_id_to_row_and_col(start)
                end_row, end_col = PromptlySheetCell.cell_id_to_row_and_col(end)
                range_values = [
                    existing_cells_dict[f"{chr(col)}{row}"].output
                    for row in range(start_row, end_row + 1)
                    for col in range(ord(start_col), ord(end_col) + 1)
                    if f"{chr(col)}{row}" in existing_cells_dict
                ]
                input_values[ref] = range_values
            elif ref in existing_cells_dict:
                input_values[ref] = existing_cells_dict[ref].output

    return input_values


def create_subsheets(formula_cells_dict, total_cols):
    formula_columns = sorted(
        set(PromptlySheetColumn.column_letter_to_index(cell.col) for cell in formula_cells_dict.values())
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


def run_sheet(sheet, run_entry, user):
    try:
        existing_cells_dict = sheet.cells
        columns_dict = {col.col: col for col in sheet.columns}
        formula_cells_dict = sheet.formula_cells
        total_rows = sheet.data.get("total_rows", 0)
        total_cols = max((PromptlySheetColumn.column_letter_to_index(col.col) for col in sheet.columns), default=0)

        async_to_sync(channel_layer.group_send)(
            str(run_entry.uuid),
            {
                "type": "sheet.status",
                "sheet": {"id": str(sheet.uuid), "running": True},
            },
        )

        subsheets = create_subsheets(formula_cells_dict, total_cols)

        for subsheet_start, subsheet_end in subsheets:
            for current_row in range(1, total_rows + 1):
                valid_cells_in_row = []
                for current_col_index in range(subsheet_start, subsheet_end + 1):
                    current_col = number_to_letters(current_col_index)
                    current_cell_id = f"{current_col}{current_row}"
                    previous_cell_id = f"{number_to_letters(current_col_index - 1)}{current_row}"

                    executed_cells = []
                    if (
                        previous_cell_id in existing_cells_dict
                        and existing_cells_dict[previous_cell_id].data
                        and existing_cells_dict[previous_cell_id].output
                    ):
                        valid_cells_in_row.append(existing_cells_dict.get(previous_cell_id))

                    if current_cell_id in formula_cells_dict:
                        input_values = process_cell_references(
                            formula_cells_dict[current_cell_id].formula.data, existing_cells_dict
                        )

                        # For formula cells, we pass entire columns data as input values
                        for col in columns_dict.values():
                            if col.col != current_col:
                                input_values[col.col] = [
                                    cell.output for cell in existing_cells_dict.values() if cell.col == col.col
                                ]

                        executed_cells = _execute_cell(
                            formula_cells_dict[current_cell_id],
                            None,
                            input_values,
                            sheet,
                            str(run_entry.uuid),
                            user,
                        )
                    elif (
                        current_col in columns_dict
                        and columns_dict[current_col].type
                        in [
                            PromptlySheetColumnType.DATA_TRANSFORMER,
                            PromptlySheetColumnType.APP_RUN,
                            PromptlySheetColumnType.PROCESSOR_RUN,
                        ]
                        and valid_cells_in_row
                    ):
                        input_values = process_cell_references(columns_dict[current_col].data, existing_cells_dict)

                        for cell in valid_cells_in_row:
                            input_values[cell.col] = cell.output

                        cell_to_execute = PromptlySheetCell(
                            row=current_row,
                            col=current_col,
                            data=columns_dict[current_col].data,
                        )
                        executed_cells = _execute_cell(
                            cell_to_execute,
                            columns_dict[current_col],
                            input_values,
                            sheet,
                            str(run_entry.uuid),
                            user,
                        )

                    # Update total rows and cols if the executed cells are beyond the current grid
                    if executed_cells:
                        sheet_grid_changed = False
                        if total_rows < max(cell.row for cell in executed_cells):
                            total_rows = max(total_rows, max(cell.row for cell in executed_cells))
                            sheet_grid_changed = True

                        if total_cols < max(
                            PromptlySheetColumn.column_letter_to_index(cell.col) for cell in executed_cells
                        ):
                            total_cols = max(
                                total_cols,
                                max(PromptlySheetColumn.column_letter_to_index(cell.col) for cell in executed_cells)
                                + 1,
                            )
                            sheet_grid_changed = True

                        if sheet_grid_changed:
                            async_to_sync(channel_layer.group_send)(
                                str(run_entry.uuid),
                                {
                                    "type": "sheet.update",
                                    "sheet": {
                                        "id": str(sheet.uuid),
                                        "total_rows": total_rows,
                                        "total_cols": total_cols,
                                    },
                                },
                            )
                            # Recompute subsheets if new columns were added
                            if total_cols > subsheet_end + 1:
                                subsheets = create_subsheets(formula_cells_dict, total_cols)
                                break

                    # Update the executed cells
                    for cell in executed_cells:
                        async_to_sync(channel_layer.group_send)(
                            str(run_entry.uuid),
                            {
                                "type": "cell.update",
                                "cell": {
                                    "id": cell.cell_id,
                                    "output": cell.output,
                                },
                            },
                        )
                        existing_cells_dict[f"{cell.col}{cell.row}"] = cell

        sheet.data["total_rows"] = total_rows
        sheet.data["total_cols"] = total_cols
        sheet.save(cells=list(existing_cells_dict.values()), update_fields=["data", "updated_at"])

        run_entry.data["total_rows"] = total_rows
        run_entry.data["total_cols"] = total_cols
        run_entry.save(cells=list(existing_cells_dict.values()), update_fields=["data"])

    except Exception:
        logger.exception("Error executing sheet")

    sheet.is_locked = False
    sheet.extra_data["running"] = False
    sheet.extra_data["job_id"] = None
    sheet.extra_data["run_id"] = None
    sheet.save(update_fields=["is_locked", "extra_data", "updated_at"])

    return DRFResponse(PromptlySheetSerializer(instance=sheet).data)


def on_sheet_run_success(job, connection, result, *args, **kwargs):
    sheet_uuid = str(job.args[0].uuid)
    run_uuid = str(job.args[1].uuid)

    async_to_sync(channel_layer.group_send)(
        run_uuid,
        {
            "type": "sheet.status",
            "sheet": {"id": str(sheet_uuid), "running": False},
        },
    )


def on_sheet_run_failed(job, connection, type, value, traceback):
    run_uuid = str(job.args[1].uuid)

    async_to_sync(channel_layer.group_send)(
        run_uuid, {"type": "sheet.error", "error": f"Sheet run failed: {str(type)} - {str(value)}"}
    )


def on_sheet_run_stopped(job, connection):
    run_uuid = str(job.args[1].uuid)

    async_to_sync(channel_layer.group_send)(run_uuid, {"type": "sheet.disconnect", "reason": "Cancelled by user"})
