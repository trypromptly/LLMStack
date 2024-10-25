import asyncio
import csv
import io
import json
import logging
import uuid
from datetime import datetime

import django_rq
from django.http import StreamingHttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response as DRFResponse
from rq import Callback

from llmstack.app_store.apis import AppStoreAppViewSet
from llmstack.apps.runner.app_runner import (
    AppRunner,
    AppRunnerRequest,
    SheetStoreAppRunnerSource,
)
from llmstack.base.models import Profile
from llmstack.common.utils.sslr._client import LLM
from llmstack.jobs.adhoc import ProcessingJob
from llmstack.jobs.models import RepeatableJob
from llmstack.sheets.models import (
    PromptlySheet,
    PromptlySheetRunEntry,
    SheetCell,
    SheetColumn,
)
from llmstack.sheets.serializers import PromptlySheetSerializer
from llmstack.sheets.yaml_loader import load_sheet_templates

logger = logging.getLogger(__name__)

SHEET_AGENT_CONFIG = {
    "name": "Promptly Sheet Agent",
    "slug": "sheet-agent",
    "version": "0.0.1",
    "description": "This agent is designed to work with Promptly Sheets. It helps fill cell values based on user provided prompts",
    "categories": ["internal"],
    "config": {
        "model": "gpt-4o-mini",
        "provider_config": {"provider": "openai", "model_name": "gpt-4o-mini"},
        "system_message": "You are Promptly Sheets Agent a large language model. You perform tasks based on user instruction. Always follow the following Guidelines 1. Never wrap your response in ```json <CODE_TEXT>```. 2. Never ask user any follow up question.",
        "max_steps": 10,
        "split_tasks": True,
        "chat_history_limit": 20,
        "temperature": 0.7,
        "seed": 1233,
        "user_message": "{{agent_instructions}}",
        "renderer_type": "Chat",
        "stream": True,
    },
    "type_slug": "agent",
    "processors": [
        {
            "id": "web_search1",
            "name": "Web Search",
            "input": {"query": ""},
            "config": {"k": 5, "search_engine": "Google"},
            "description": "Search the web for answers",
            "provider_slug": "promptly",
            "processor_slug": "web_search",
            "output_template": {
                "markdown": "{% for result in results %}\n{{result.text}}\n{{result.source}}\n\n{% endfor %}"
            },
        }
    ],
    "input_fields": [
        {
            "name": "agent_instructions",
            "type": "multi",
            "title": "Task",
            "required": True,
            "allowFiles": False,
            "description": "What do you want the agent to perform?",
            "placeholder": "Type in your message",
        }
    ],
    "output_template": {"markdown": "{{agent.content}}", "jsonpath": "$.agent.content"},
}


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
            cell = row_cells.get(f"{column.col_letter}{row}")
            row_values.append(cell.value if cell else "")

        writer.writerow(row_values)
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)


class PromptlySheetAppExecuteJob(ProcessingJob):
    @classmethod
    def get_connection(self):
        if self._use_redis:
            return django_rq.get_connection("sheets")
        else:
            return "local"  # Return a dummy connection

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
                "columns": [SheetColumn(**column_data).model_dump() for column_data in request.data.get("columns", [])],
                "total_rows": request.data.get("total_rows", 0),
                "total_columns": request.data.get("total_columns", 26),
            },
            extra_data=request.data.get("extra_data", {"has_header": True}),
        )

        if "cells" in request.data:
            cells = [SheetCell(**cell_data) for cell_data in request.data.get("cells", {}).values()]
            sheet.save(cells=cells, update_fields=["data"])

        return DRFResponse(PromptlySheetSerializer(instance=sheet).data)

    def delete(self, request, sheet_uuid=None):
        profile = Profile.objects.get(user=request.user)

        sheet = PromptlySheet.objects.get(uuid=sheet_uuid, profile_uuid=profile.uuid)

        # Delete associated PromptlySheetRunEntry entries
        PromptlySheetRunEntry.objects.filter(sheet_uuid=sheet.uuid).delete()
        if sheet.extra_data.get("scheduled_run_config"):
            repeat_job_id = sheet.extra_data["scheduled_run_config"]["job_id"]
            try:
                job = RepeatableJob.objects.get(uuid=repeat_job_id)
                job.delete()
            except RepeatableJob.DoesNotExist:
                pass

        sheet.delete()

        return DRFResponse(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, sheet_uuid=None):
        profile = Profile.objects.get(user=request.user)

        sheet = PromptlySheet.objects.get(uuid=sheet_uuid, profile_uuid=profile.uuid)
        sheet.name = request.data.get("name", sheet.name)
        sheet.extra_data = request.data.get("extra_data", sheet.extra_data)

        if "scheduled_run_config" in request.data:
            if request.data["scheduled_run_config"] is None and sheet.extra_data.get("scheduled_run_config"):
                # We are deleting a scheduled run, delete the job
                repeat_job_id = sheet.extra_data["scheduled_run_config"]["job_id"]
                try:
                    job = RepeatableJob.objects.get(uuid=repeat_job_id)
                    job.delete()
                except RepeatableJob.DoesNotExist:
                    pass
                sheet.extra_data["scheduled_run_config"] = None
            elif request.data["scheduled_run_config"]:
                # Create a new job
                scheduled_time = datetime.strptime(
                    request.data["scheduled_run_config"]["start_time"].replace("Z", "+00:00"),
                    "%Y-%m-%dT%H:%M:%S.%f%z",
                )
                job_args = {
                    "name": f"Sheet_{sheet.name[:4]}_automated_run_{sheet.uuid}",
                    "callable": "llmstack.sheets.tasks.scheduled_run_sheet",
                    "callable_args": json.dumps([str(sheet.uuid), request.user.id]),
                    "callable_kwargs": json.dumps({}),
                    "enabled": True,
                    "queue": "sheets",
                    "result_ttl": 86400,
                    "owner": request.user,
                    "scheduled_time": scheduled_time,
                    "task_category": "data_refresh",
                }
                repeat_interval = 7 if request.data["scheduled_run_config"]["type"] == "weekly" else 1
                job = RepeatableJob(
                    interval=repeat_interval,
                    interval_unit="days",
                    **job_args,
                )
                job.save()
                scheduled_run_config = {}
                scheduled_run_config["job_id"] = str(job.uuid)
                scheduled_run_config["start_time"] = request.data["scheduled_run_config"]["start_time"]
                scheduled_run_config["type"] = request.data["scheduled_run_config"]["type"]
                scheduled_run_config["time"] = request.data["scheduled_run_config"]["time"]
                if "day" in request.data["scheduled_run_config"]:
                    scheduled_run_config["day"] = request.data["scheduled_run_config"]["day"]
                sheet.extra_data["scheduled_run_config"] = scheduled_run_config

        if "total_rows" in request.data:
            sheet.data["total_rows"] = request.data["total_rows"]

        if "total_columns" in request.data:
            sheet.data["total_columns"] = request.data["total_columns"]

        if "description" in request.data:
            sheet.data["description"] = request.data["description"]

        if "columns" in request.data:
            sheet.data["columns"] = [SheetColumn(**column_data).model_dump() for column_data in request.data["columns"]]

        sheet.save()

        if "cells" in request.data:
            cell_data = request.data.get("cells", {}).values()

            cells = [SheetCell(**cell_data) for cell_data in cell_data]
            sheet.save(cells=cells, update_fields=["data"])

        return DRFResponse(PromptlySheetSerializer(instance=sheet).data)

    def run_async(self, request, sheet_uuid=None):
        profile = Profile.objects.get(user=request.user)
        selected_grid = request.data.get("selected_grid")
        sheet = PromptlySheet.objects.get(uuid=sheet_uuid, profile_uuid=profile.uuid)
        if sheet.is_locked:
            return DRFResponse(
                {"detail": "The sheet is locked and cannot be run at this time."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        run_entry = PromptlySheetRunEntry(sheet_uuid=sheet.uuid, profile_uuid=profile.uuid)
        run_entry.save()

        job = PromptlySheetAppExecuteJob.create(
            func="llmstack.sheets.tasks.run_sheet",
            args=[str(sheet.uuid), str(run_entry.uuid), request.user.id, selected_grid],
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

    def _run_until_complete(self, app_runner, input_data, session_id):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = app_runner.run_until_complete(
            AppRunnerRequest(client_request_id=str(uuid.uuid4()), session_id=session_id, input=input_data), loop
        )
        loop.close()
        return response.data.model_dump()

    def _execute_processor_run_cell(self, request, provider_slug, processor_slug, sheet_id, input_data, config_data):
        from llmstack.apps.apis import PlaygroundViewSet
        from llmstack.apps.runner.app_runner import SheetProcessorRunnerSource

        session_id = str(uuid.uuid4())
        app_runner = PlaygroundViewSet().get_app_runner(
            session_id,
            source=SheetProcessorRunnerSource(
                request_user_email=request.user.email,
                request_user=request.user,
                provider_slug=provider_slug,
                processor_slug=processor_slug,
                sheet_id=sheet_id,
            ),
            request_user=request.user,
            input_data=input_data,
            config_data=config_data,
        )
        run_response = self._run_until_complete(app_runner, input_data, session_id)
        if "output" in run_response and run_response.get("chunks", {}).get("processor"):
            return {"output": run_response.get("chunks", {}).get("processor")}
        elif "errors" in run_response:
            return {"errors": run_response.get("errors")}
        return {"errors": "Processor run failed."}

    def _execute_app_run_cell(self, request, app_slug, input_data, sheet_id):
        session_id = str(uuid.uuid4())
        app_runner = AppStoreAppViewSet().get_app_runner(
            session_id=session_id,
            app_slug=app_slug,
            source=SheetStoreAppRunnerSource(
                request_user_email=request.user.email,
                request_user=request.user,
                sheet_id=sheet_id,
                slug=app_slug,
            ),
            request_user=request.user,
        )

        run_response = self._run_until_complete(app_runner, input_data, session_id)
        if "output" in run_response and "output" in run_response["output"]:
            return {"output": run_response.get("output").get("output")}
        elif "errors" in run_response:
            return {"errors": run_response.get("errors")}
        return {"errors": "App run failed."}

    def _execute_agent_run_cell(self, request, input_data, config_data, sheet_id):
        session_id = str(uuid.uuid4())
        app_run_user_profile = Profile.objects.get(user=request.user)
        vendor_env = {
            "provider_configs": app_run_user_profile.get_merged_provider_configs(),
            "connections": app_run_user_profile.connections,
        }

        app_runner = AppRunner(
            session_id=session_id,
            app_data=SHEET_AGENT_CONFIG,
            source=SheetStoreAppRunnerSource(
                request_user_email=request.user.email,
                request_user=request.user,
                sheet_id=sheet_id,
                slug="sheet_agent",
            ),
            vendor_env=vendor_env,
        )
        run_response = self._run_until_complete(app_runner, input_data, session_id)

        if "output" in run_response and "output" in run_response["output"]:
            return {"output": run_response.get("output").get("output")}
        elif "errors" in run_response:
            return {"errors": run_response.get("errors")}
        return {"errors": "App run failed."}

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
