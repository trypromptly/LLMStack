import uuid

from django.db import models


class PromptlySheet(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile_uuid = models.UUIDField(blank=False, null=False, help_text="The UUID of the owner of the sheet")
    name = models.CharField(max_length=255, blank=False, null=False, help_text="The name of the sheet")
    extra_data = models.JSONField(blank=True, null=True, help_text="Extra data for the sheet")
    created_at = models.DateTimeField(auto_now_add=True, help_text="The date and time the sheet was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="The date and time the sheet was last updated")

    class Meta:
        indexes = [
            models.Index(fields=["profile_uuid"]),
        ]

    @property
    def cells(self):
        return PromptlySheetCell.objects.filter(sheet=self)

    def __str__(self):
        return self.name


class PromptlySheetCell(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sheet = models.ForeignKey(PromptlySheet, on_delete=models.DO_NOTHING, related_name="cells")
    row = models.IntegerField(blank=False, null=False, help_text="The row of the cell")
    column = models.IntegerField(blank=False, null=False, help_text="The column of the cell")
    value = models.TextField(blank=True, null=True, help_text="The value of the cell")
    value_type = models.CharField(max_length=255, blank=True, null=True, help_text="The type of the value of the cell")
    extra_data = models.JSONField(blank=True, null=True, help_text="Extra data for the cell")
    created_at = models.DateTimeField(auto_now_add=True, help_text="The date and time the cell was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="The date and time the cell was last updated")

    class Meta:
        indexes = [
            models.Index(fields=["sheet", "row", "column"]),
        ]

    @property
    def is_header(self):
        return self.row == 0 and self.extra_data.get("is_header", False)

    @property
    def is_formula(self):
        return self.value.startswith("=")

    @property
    def display_value(self):
        return self.value if not self.is_formula else self.extra_data.get("display_value", "")

    def __str__(self):
        return f"{self.sheet.name} - {self.row} - {self.column}"
