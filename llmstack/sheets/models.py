import base64
import json
import uuid
from typing import Dict

from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from pydantic import BaseModel

from llmstack.assets.models import Assets


class PromptlySheetCell(BaseModel):
    row: int
    col: int
    value: str = ""
    value_type: str = "string"
    extra_data: dict = {}

    @property
    def is_formula(self):
        return self.value.startswith("=")

    @property
    def cell_id(self):
        return f"{self.col}-{self.row}"

    def model_dump(
        self,
        *,
        mode="python",
        include=None,
        exclude=None,
        context=None,
        by_alias=False,
        exclude_unset=False,
        exclude_defaults=False,
        exclude_none=False,
        round_trip=False,
        warnings=True,
        serialize_as_any=False,
    ):
        model_dict = super().model_dump(
            mode=mode,
            include=include,
            exclude=exclude,
            context=context,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
            serialize_as_any=serialize_as_any,
        )
        model_dict["cell_id"] = self.cell_id
        return model_dict


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


def create_sheet_data_objrefs(
    cells: Dict[int, Dict[int, PromptlySheetCell]], sheet_name, sheet_uuid, page_size: int = 1000
):
    for i in range(0, len(cells), page_size):
        chunk = {}
        for j in range(i, min(i + page_size, len(cells))):
            chunk[j] = dict(map(lambda entry: (entry[0], entry[1].model_dump()), cells[j].items()))

        data_json = json.dumps(chunk)
        filename = f"{sheet_name}_{str(uuid.uuid4())[:4]}_{i}.json"
        data_json_uri = f"data:application/json;name={filename};base64,{base64.b64encode(data_json.encode()).decode()}"
        file_obj = PromptlySheetFiles.create_from_data_uri(
            data_json_uri, ref_id=sheet_uuid, metadata={"sheet_uuid": sheet_uuid}
        )
        yield f"objref://sheets/{file_obj.uuid}"


def get_sheet_cells(objref):
    try:
        category, uuid = objref.strip().split("//")[1].split("/")
        asset = PromptlySheetFiles.objects.get(uuid=uuid)
        with asset.file.open("rb") as f:
            cells = json.load(f)

            return dict(
                map(
                    lambda row_entry: (
                        int(row_entry[0]),
                        (
                            dict(
                                map(
                                    lambda cell_entry: (int(cell_entry[0]), PromptlySheetCell(**cell_entry[1])),
                                    row_entry[1].items(),
                                )
                            )
                        ),
                    ),
                    cells.items(),
                )
            )

    except Exception:
        pass


class PromptlySheet(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile_uuid = models.UUIDField(blank=False, null=False, help_text="The UUID of the owner of the sheet")
    name = models.CharField(max_length=255, blank=False, null=False, help_text="The name of the sheet")
    extra_data = models.JSONField(blank=True, null=True, help_text="Extra data for the sheet")
    data = models.JSONField(blank=True, null=True, help_text="The data of the sheet", default={"cells": []})
    is_locked = models.BooleanField(default=False, help_text="Whether the sheet is locked")
    created_at = models.DateTimeField(auto_now_add=True, help_text="The date and time the sheet was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="The date and time the sheet was last updated")

    class Meta:
        indexes = [
            models.Index(fields=["profile_uuid"]),
        ]

    def __str__(self):
        return self.name

    def get_cell(self, row, col):
        page_size = self.extra_data.get("page_size", 1000)
        page = row // page_size
        pages = self.data.get("cells", [])
        page_objref = pages[page]
        cells = get_sheet_cells(page_objref)
        return cells[row % page_size][col]

    @property
    def cells(self):
        for objref in self.data.get("cells", []):
            cells = get_sheet_cells(objref)
            yield cells

    @property
    def rows(self):
        for objref in self.data.get("cells", []):
            cells = get_sheet_cells(objref)
            for cell_row in cells:
                yield (cell_row, cells[cell_row])

    def save(self, *args, **kwargs):
        if kwargs.get("cells"):
            if self.data and self.data.get("cells"):
                # Delete the older objrefs
                delete_sheet_data_objrefs(self.data.get("cells", []))
            cell_objs = kwargs.pop("cells")
            self.data = {
                "cells": list(
                    create_sheet_data_objrefs(
                        cell_objs, self.name, str(self.uuid), page_size=self.extra_data.get("page_size", 1000)
                    )
                )
            }
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

        cell_objs = kwargs.pop("cells", {})
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
