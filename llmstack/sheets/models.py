import base64
import json
import logging
import string
import uuid
from enum import Enum
from functools import cache
from typing import List, Optional

from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from pydantic import BaseModel

from llmstack.assets.models import Assets

logger = logging.getLogger(__name__)


class PromptlySheetColumnType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    DURATION = "duration"
    PERCENTAGE = "percentage"
    CURRENCY = "currency"
    URL = "url"
    EMAIL = "email"
    PHONE = "phone"
    IMAGE = "image"
    FILE = "file"
    FORMULA = "formula"
    APP_RUN = "app_run"
    PROCESSOR_RUN = "processor_run"

    def __str__(self):
        return self.value


class PromptlySheetColumn(BaseModel):
    title: str
    kind: PromptlySheetColumnType = PromptlySheetColumnType.TEXT
    data: dict = {}
    col: str
    width: Optional[int] = None

    @staticmethod
    def column_index_to_letter(index):
        result = ""
        while index > 0:
            index -= 1
            result = string.ascii_uppercase[index % 26] + result
            index //= 26
        return result or "A"

    @staticmethod
    def column_letter_to_index(letter):
        return sum((ord(c) - 64) * (26**i) for i, c in enumerate(reversed(letter.upper()))) - 1

    def __init__(self, **data):
        super().__init__(**data)
        if isinstance(self.col, int):
            self.col = self.column_index_to_letter(self.col)

    class Config:
        json_encoders = {
            PromptlySheetColumnType: lambda v: v.value,
        }


class PromptlySheetCell(BaseModel):
    row: int
    col: str
    data: dict = {}
    display_data: str = ""
    formula: str = ""

    @property
    def is_formula(self):
        return bool(self.formula)

    @property
    def cell_id(self):
        return f"{self.col}{self.row}"

    @staticmethod
    def column_index_to_letter(index):
        result = ""
        while index > 0:
            index -= 1
            result = string.ascii_uppercase[index % 26] + result
            index //= 26
        return result or "A"

    @staticmethod
    def column_letter_to_index(letter):
        return sum((ord(c) - 64) * (26**i) for i, c in enumerate(reversed(letter.upper()))) - 1


class PromptlySheetFiles(Assets):
    def select_storage():
        from django.core.files.storage import storages

        return storages["assets"]

    def sheet_upload_to(instance, filename):
        return "/".join(["sheets", str(instance.ref_id), filename])

    ref_id = models.UUIDField(help_text="UUID of the sheet this file belongs to", blank=True, null=False)
    file = models.FileField(
        storage=select_storage,
        upload_to=sheet_upload_to,
        null=True,
        blank=True,
    )

    @property
    def category(self):
        return "sheets"

    @classmethod
    def is_accessible(asset, request_user, request_session):
        return True


def delete_sheet_data_objrefs(data_objrefs):
    for objref in data_objrefs:
        try:
            category, uuid = objref.strip().split("//")[1].split("/")
            asset = PromptlySheetFiles.objects.get(uuid=uuid)
            asset.delete()
        except Exception:
            pass


def create_sheet_data_objrefs(cell_objs: List[PromptlySheetCell], sheet_name, sheet_uuid, page_size: int = 1000):
    # Sort the cells by row and columns
    cells = sorted(cell_objs, key=lambda cell: (cell.row, cell.col))
    max_rows = max(cell_objs, key=lambda cell: cell.row).row + 1

    for i in range(0, max_rows, page_size):
        chunk = {}
        cells_in_page = list(filter(lambda cell: cell.row >= i and cell.row < i + page_size, cells))
        for cell in cells_in_page:
            chunk[cell.cell_id] = cell.model_dump()

        data_json = json.dumps(chunk)
        filename = f"{sheet_name}_{str(uuid.uuid4())[:4]}_{i}.json"
        data_json_uri = f"data:application/json;name={filename};base64,{base64.b64encode(data_json.encode()).decode()}"
        file_obj = PromptlySheetFiles.create_from_data_uri(
            data_json_uri, ref_id=sheet_uuid, metadata={"sheet_uuid": sheet_uuid}
        )
        yield f"objref://sheets/{file_obj.uuid}"


class PromptlySheet(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile_uuid = models.UUIDField(blank=False, null=False, help_text="The UUID of the owner of the sheet")
    name = models.CharField(max_length=255, blank=False, null=False, help_text="The name of the sheet")
    extra_data = models.JSONField(blank=True, null=True, help_text="Extra data for the sheet")
    data = models.JSONField(blank=True, null=True, help_text="The data of the sheet", default=dict)
    is_locked = models.BooleanField(default=False, help_text="Whether the sheet is locked")
    created_at = models.DateTimeField(auto_now_add=True, help_text="The date and time the sheet was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="The date and time the sheet was last updated")

    class Meta:
        indexes = [
            models.Index(fields=["profile_uuid"]),
        ]

    def __str__(self):
        return self.name

    @cache
    def get_sheet_cells(self, objref):
        try:
            category, uuid = objref.strip().split("//")[1].split("/")
            asset = PromptlySheetFiles.objects.get(uuid=uuid)
            cells = {}
            with asset.file.open("rb") as f:
                data = json.load(f)
                for cell_id, cell_data in data.items():
                    cells[cell_id] = PromptlySheetCell(**cell_data)

                return cells

        except Exception as e:
            logger.error(f"Error loading sheet data from objref: {e}")
            pass

        return {}

    def get_cell(self, row, col):
        page_size = self.extra_data.get("page_size", 1000)
        page = row // page_size
        pages = self.data.get("cells", [])
        page_objref = pages[page]
        cells = self.get_sheet_cells(page_objref)
        return cells.get(f"{col}{row}", {})

    @property
    def cells(self):
        cells = {}
        for objref in self.data.get("cells", []):
            cells.update(self.get_sheet_cells(objref))

        return cells

    @property
    def columns(self):
        return [PromptlySheetColumn(**column) for column in self.data.get("columns", [])]

    def update_total_rows(self, total_rows):
        self.data["total_rows"] = total_rows
        self.save(update_fields=["data"])

    def save(self, *args, **kwargs):
        if "cells" in kwargs:
            if self.data and self.data.get("cells"):
                # Delete the older objrefs
                delete_sheet_data_objrefs(self.data.get("cells", []))
            cell_objs = kwargs.pop("cells")

            self.data["cells"] = (
                list(
                    create_sheet_data_objrefs(
                        cell_objs, self.name, str(self.uuid), page_size=self.extra_data.get("page_size", 1000)
                    )
                )
                if cell_objs
                else []
            )
            if kwargs.get("update_fields"):
                kwargs["update_fields"].append("data")

        super().save(*args, **kwargs)


class PromptlySheetRunEntry(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile_uuid = models.UUIDField(blank=False, null=False, help_text="The UUID of the owner of the sheet")
    sheet_uuid = models.UUIDField(blank=False, null=False, help_text="The UUID of the sheet")
    data = models.JSONField(blank=True, null=True, help_text="The data of the sheet", default={"cells": []})
    created_at = models.DateTimeField(auto_now_add=True, help_text="The date and time the run was created")

    class Meta:
        indexes = [
            models.Index(fields=["profile_uuid"]),
            models.Index(fields=["sheet_uuid"]),
        ]

    def __str__(self):
        return str(self.uuid)

    def save(self, *args, **kwargs):
        sheet = PromptlySheet.objects.get(uuid=self.sheet_uuid)

        cell_objs = kwargs.pop("cells", [])
        if not cell_objs:
            self.data = {"cells": []}
        else:
            # Convert column letters to indices before saving
            for cell in cell_objs:
                cell.col = PromptlySheetCell.column_letter_to_index(cell.col)

            self.data = {
                "cells": list(
                    create_sheet_data_objrefs(
                        cell_objs,
                        f"{sheet.name}_processed",
                        str(sheet.uuid),
                        page_size=sheet.extra_data.get("page_size", 1000),
                    )
                )
            }

        if kwargs.get("update_fields"):
            kwargs["update_fields"].append("data")

        super().save(*args, **kwargs)


@receiver(post_delete, sender=PromptlySheet)
def register_sheet_delete(sender, instance: PromptlySheet, **kwargs):
    if instance.data:
        delete_sheet_data_objrefs(instance.data.get("cells", []))


@receiver(post_delete, sender=PromptlySheetRunEntry)
def register_sheet_run_entry_delete(sender, instance: PromptlySheetRunEntry, **kwargs):
    if instance.data:
        delete_sheet_data_objrefs(instance.data.get("cells", []))
