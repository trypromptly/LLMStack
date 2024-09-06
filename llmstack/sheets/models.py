import base64
import json
import logging
import string
import uuid
from enum import Enum
from functools import cache
from typing import Any, List, Optional, Union

from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from pydantic import BaseModel

from llmstack.assets.models import Assets

logger = logging.getLogger(__name__)


class SheetCellType(int, Enum):
    TEXT = 0
    NUMBER = 1
    BOOLEAN = 2
    IMAGE = 3
    URI = 4
    BUBBLE = 5

    def __str__(self):
        return self.value


class SheetCellStatus(int, Enum):
    READY = 0
    PROCESSING = 1
    ERROR = 2

    def __str__(self):
        return self.value


class SheetFormulaType(int, Enum):
    NONE = 0
    DATA_TRANSFORMER = 1
    APP_RUN = 2
    PROCESSOR_RUN = 3

    def __str__(self):
        return self.value


class SheetFormulaData(BaseModel):
    pass


class NoneFormulaData(SheetFormulaData):
    pass


class AppRunFormulaData(SheetFormulaData):
    app_slug: str
    input: dict = {}


class ProcessorRunFormulaData(SheetFormulaData):
    provider_slug: str
    processor_slug: str
    input: dict = {}
    config: dict = {}
    output_template: dict = {
        "markdown": "",
    }


class DataTransformerFormulaData(SheetFormulaData):
    transformation_template: str


class SheetFormula(BaseModel):
    type: SheetFormulaType = SheetFormulaType.NONE
    data: Union[NoneFormulaData, AppRunFormulaData, ProcessorRunFormulaData, DataTransformerFormulaData]


class SheetColumn(BaseModel):
    title: str
    col_letter: str
    cell_type: SheetCellType = SheetCellType.TEXT
    position: int = 0
    width: int = 300
    formula: Optional[SheetFormula] = None

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
        if "formula" in data and isinstance(data["formula"], dict):
            formula_type = SheetFormulaType(data["formula"]["type"])
            formula_data = data["formula"]["data"]

            if formula_type == SheetFormulaType.PROCESSOR_RUN:
                data["formula"] = SheetFormula(type=formula_type, data=ProcessorRunFormulaData(**formula_data))
            elif formula_type == SheetFormulaType.APP_RUN:
                data["formula"] = SheetFormula(type=formula_type, data=AppRunFormulaData(**formula_data))
            elif formula_type == SheetFormulaType.DATA_TRANSFORMER:
                data["formula"] = SheetFormula(type=formula_type, data=DataTransformerFormulaData(**formula_data))
            else:
                data["formula"] = SheetFormula(type=SheetFormulaType.NONE, data=NoneFormulaData())

        if "cell_type" in data and isinstance(data["cell_type"], int):
            data["cell_type"] = SheetCellType(data["cell_type"])

        super().__init__(**data)
        if isinstance(self.col_letter, int):
            self.col_letter = self.column_index_to_letter(self.col_letter)

    class Config:
        json_encoders = {
            SheetCellType: lambda v: v.value,
        }


class SheetCell(BaseModel):
    row: int
    col_letter: str
    status: SheetCellStatus = SheetCellStatus.READY
    error: Optional[str] = None
    value: Optional[Any] = None
    formula: Optional[SheetFormula] = None
    spread_output: bool = False

    def __init__(self, **data):
        if "formula" in data and isinstance(data["formula"], dict):
            formula_type = SheetFormulaType(data["formula"]["type"])
            formula_data = data["formula"]["data"]

            if formula_type == SheetFormulaType.PROCESSOR_RUN:
                data["formula"] = SheetFormula(type=formula_type, data=ProcessorRunFormulaData(**formula_data))
            else:
                data["formula"] = SheetFormula(type=SheetFormulaType.NONE, data=NoneFormulaData())

        if "cell_type" in data and isinstance(data["cell_type"], int):
            data["cell_type"] = SheetCellType(data["cell_type"])

        super().__init__(**data)
        if isinstance(self.col_letter, int):
            self.col_letter = self.column_index_to_letter(self.col_letter)

    @property
    def cell_id(self):
        return f"{self.col_letter}{self.row}"

    @property
    def has_output(self):
        return bool(self.value)

    @property
    def is_formula(self):
        return bool(self.formula)

    @property
    def output(self):
        return self.value

    @classmethod
    def cell_id_to_row_and_col(cls, cell_id):
        # Split the cell_id into letter and number parts
        letter_part = "".join(filter(str.isalpha, cell_id))
        number_part = "".join(filter(str.isdigit, cell_id))

        # Convert the number part to row
        row = int(number_part)

        return (row, letter_part)


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


def create_sheet_data_objrefs(cell_objs: List[SheetCell], sheet_name, sheet_uuid, page_size: int = 1000):
    # Sort the cells by row and columns
    cells = sorted(cell_objs, key=lambda cell: (cell.row, SheetColumn.column_letter_to_index(cell.col_letter)))
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
                cell_items = data.items() if isinstance(data, dict) else enumerate(data)
                for cell_id, cell_data in cell_items:
                    cells[cell_id] = SheetCell(**cell_data)

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
        return [SheetColumn(**column) for column in self.data.get("columns", [])]

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
