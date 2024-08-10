# Generated by Django 4.2.14 on 2024-08-10 14:51

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PromptlySheet',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('profile_uuid', models.UUIDField(help_text='The UUID of the owner of the sheet')),
                ('name', models.CharField(help_text='The name of the sheet', max_length=255)),
                ('extra_data', models.JSONField(blank=True, help_text='Extra data for the sheet', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The date and time the sheet was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='The date and time the sheet was last updated')),
            ],
        ),
        migrations.CreateModel(
            name='PromptlySheetCell',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('row', models.IntegerField(help_text='The row of the cell')),
                ('column', models.IntegerField(help_text='The column of the cell')),
                ('value', models.TextField(blank=True, help_text='The value of the cell', null=True)),
                ('value_type', models.CharField(blank=True, help_text='The type of the value of the cell', max_length=255, null=True)),
                ('extra_data', models.JSONField(blank=True, help_text='Extra data for the cell', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The date and time the cell was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='The date and time the cell was last updated')),
                ('sheet', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='cells', to='promptly_sheets.promptlysheet')),
            ],
        ),
        migrations.AddIndex(
            model_name='promptlysheet',
            index=models.Index(fields=['profile_uuid'], name='promptly_sh_profile_38dc1d_idx'),
        ),
        migrations.AddIndex(
            model_name='promptlysheetcell',
            index=models.Index(fields=['sheet', 'row', 'column'], name='promptly_sh_sheet_i_10c000_idx'),
        ),
    ]
