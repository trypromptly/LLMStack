import ast
import json
import logging
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

    response = None
    fill_rows_with_output = not is_formula_cell and column.data.get("fill_rows_with_output", False)
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
                response["output"] = hydrate_input(processor_output_template, processor_output)
            except Exception as e:
                logger.error(f"Error rendering output template: {e}")
                pass

    output = response.get("output", "") if execution_type != "data_transformer" else ""

    # Apply transformation template if present
    transformation_template = execution_data.get("transformation_template")
    if transformation_template:
        try:
            output = render_template(
                transformation_template,
                input_values if execution_type == "data_transformer" else {"output": output},
            )
        except Exception as e:
            logger.error(f"Error applying transformation template: {e}")
            async_to_sync(channel_layer.group_send)(
                run_id, {"type": "cell.error", "cell": {"id": cell.cell_id, "error": str(e)}}
            )

    # Fill rows with output if we are executing the column for the first time
    if fill_rows_with_output and len(input_values.values()) == 0 and cell.row == 1:
        try:
            output_list = json.loads(output) if isinstance(output, str) else output
            if isinstance(output_list, list):
                output_list = [
                    PromptlySheetCell(
                        row=cell.row + i,
                        col=cell.col,
                        data={"output": str(item)},
                    )
                    for i, item in enumerate(output_list)
                ]

                # If we have more rows than total_rows, we need to update the total_rows and send a message to the frontend
                if len(output_list) > sheet.data.get("total_rows", 0):
                    sheet.update_total_rows(len(output_list))

                    async_to_sync(channel_layer.group_send)(
                        run_id,
                        {
                            "type": "sheet.update",
                            "sheet": {"id": str(sheet.uuid), "total_rows": len(output_list)},
                        },
                    )

                for cell in output_list:
                    async_to_sync(channel_layer.group_send)(
                        run_id,
                        {
                            "type": "cell.update",
                            "cell": {
                                "id": cell.cell_id,
                                "output": cell.data.get("output", "") if isinstance(cell.data, dict) else cell.data,
                            },
                        },
                    )

                return output_list
            else:
                cell.data = {"output": str(output)}
                return [cell]
        except json.JSONDecodeError:
            cell.data = {"output": str(output)}
            return [cell]
    else:
        cell.data = {"output": str(output)}
        async_to_sync(channel_layer.group_send)(
            run_id,
            {
                "type": "cell.update",
                "cell": {
                    "id": cell.cell_id,
                    "output": cell.data.get("output", "") if isinstance(cell.data, dict) else cell.data,
                },
            },
        )
        return [cell]


def run_sheet(sheet, run_entry, user):
    try:
        existing_cells_dict = sheet.cells
        existing_cols = sheet.columns

        async_to_sync(channel_layer.group_send)(
            str(run_entry.uuid),
            {
                "type": "sheet.status",
                "sheet": {"id": str(sheet.uuid), "running": True},
            },
        )

        # Execute cells that are not dependent on other cells
        for column in existing_cols:
            if column.type not in ["app_run", "processor_run", "data_transformer"]:
                continue

            fill_rows_with_output = column.data.get("fill_rows_with_output", False)
            if fill_rows_with_output:
                cell_to_execute = PromptlySheetCell(
                    row=1,
                    col=column.col,
                    kind=column.kind,
                )
                executed_cells = _execute_cell(
                    cell_to_execute,
                    column,
                    {},
                    sheet,
                    str(run_entry.uuid),
                    user,
                )
                for cell in executed_cells:
                    existing_cells_dict[f"{cell.col}{cell.row}"] = cell

        # Execute cells that are dependent on other cells
        for row_number in range(1, sheet.data.get("total_rows", 0) + 1):
            for col in existing_cols:
                if col.type not in ["app_run", "processor_run", "data_transformer"]:
                    continue

                # Skip if this column is to fill rows with output
                if col.data.get("fill_rows_with_output", False):
                    continue

                valid_cells_in_row = [
                    existing_cells_dict.get(f"{col.col}{row_number}")
                    for col in existing_cols
                    if existing_cells_dict.get(f"{col.col}{row_number}")
                ]

                # Skip if none of the cells have any valid data["output"]
                if not any(cell.is_output for cell in valid_cells_in_row):
                    continue

                cell_to_execute = PromptlySheetCell(
                    row=row_number,
                    col=col.col,
                    data=col.data,
                )
                executed_cells = _execute_cell(
                    cell_to_execute,
                    col,
                    {cell.col: cell.output for cell in valid_cells_in_row},
                    sheet,
                    str(run_entry.uuid),
                    user,
                )
                for cell in executed_cells:
                    existing_cells_dict[f"{cell.col}{cell.row}"] = cell

        # Execute formula cells
        for cell_id, formula_cell in sheet.formula_cells.items():
            input_values = {}

            def process_formula_data(data):
                if isinstance(data, dict):
                    for key, value in data.items():
                        process_formula_data(value)
                elif isinstance(data, list):
                    for item in data:
                        process_formula_data(item)
                elif isinstance(data, str):
                    # Extract cell references and ranges from the string
                    import re

                    cell_refs = re.findall(r"([A-Z]+\d+(?:-[A-Z]+\d+)?)", data)
                    for ref in cell_refs:
                        if "-" in ref:
                            start, end = ref.split("-")
                            start_row, start_col = PromptlySheetCell.cell_id_to_row_and_col(start)
                            end_row, end_col = PromptlySheetCell.cell_id_to_row_and_col(end)
                            range_values = []
                            for row in range(start_row, end_row + 1):
                                for col in range(ord(start_col), ord(end_col) + 1):
                                    cell_id = f"{chr(col)}{row}"
                                    if cell_id in existing_cells_dict:
                                        range_values.append(existing_cells_dict[cell_id].output)
                            input_values[ref] = range_values
                        else:
                            if ref in existing_cells_dict:
                                input_values[ref] = existing_cells_dict[ref].output

            # Start the recursive process with the formula data
            process_formula_data(formula_cell.formula.data)

            executed_cells = _execute_cell(
                formula_cell,
                None,
                input_values,
                sheet,
                str(run_entry.uuid),
                user,
            )

            for cell in executed_cells:
                existing_cells_dict[f"{cell.col}{cell.row}"] = cell

        sheet.save(cells=list(existing_cells_dict.values()), update_fields=["updated_at"])
        run_entry.save(cells=list(existing_cells_dict.values()))

    except Exception:
        logger.exception("Error executing sheet")

    sheet.extra_data["running"] = False
    sheet.is_locked = False
    sheet.save(update_fields=["is_locked", "extra_data"])

    async_to_sync(channel_layer.group_send)(
        str(run_entry.uuid),
        {
            "type": "sheet.status",
            "sheet": {"id": str(sheet.uuid), "running": False},
        },
    )

    return DRFResponse(PromptlySheetSerializer(instance=sheet).data)
