import logging
import time
import uuid
from concurrent.futures import Future

from django.shortcuts import get_object_or_404
from flags.state import flag_enabled
from rest_framework import viewsets
from rest_framework.response import Response as DRFResponse
from rq.job import Job

from llmstack.data.yaml_loader import get_data_pipelines_from_contrib
from llmstack.jobs.adhoc import AddDataSourceEntryJob, ExtractURLJob

from .models import DataSource, DataSourceEntry, DataSourceEntryStatus, DataSourceType
from .serializers import DataSourceEntrySerializer, DataSourceSerializer
from .tasks import extract_urls_task

logger = logging.getLogger(__name__)


def get_data_source_type(slug):
    return DataSourceTypeViewSet().get(None, slug).data


def load_sources():
    from llmstack.data.sources.files.file import FileSchema
    from llmstack.data.sources.files.pdf import PdfSchema
    from llmstack.data.sources.text.text_data import TextSchema
    from llmstack.data.sources.website.url import URLSchema

    sources = {}
    for cls in [FileSchema, PdfSchema, TextSchema, URLSchema]:
        if not sources.get(cls.provider_slug()):
            sources[cls.provider_slug()] = {}
        sources[cls.provider_slug()][cls.slug()] = {
            "slug": cls.slug(),
            "provider_slug": cls.provider_slug(),
            "schema": cls.get_schema(),
            "ui_schema": cls.get_ui_schema(),
        }
    return sources


class DataSourceTypeViewSet(viewsets.ViewSet):
    def list(self, request):
        processors = []

        sources = load_sources()
        pipeline_templates = get_data_pipelines_from_contrib()

        for pipeline_template in pipeline_templates:
            source = pipeline_template.pipeline.source
            if source:
                source_schema = sources.get(source.provider_slug, {}).get(source.slug, {}).get("schema", {})
                source_ui_schema = sources.get(source.provider_slug, {}).get(source.slug, {}).get("ui_schema", {})
            else:
                source_schema = {}
                source_ui_schema = {}
            is_external_datasource = (
                pipeline_template.pipeline.source is None
                and pipeline_template.pipeline.transformations is None
                and pipeline_template.pipeline.destination
            )
            processors.append(
                {
                    "slug": pipeline_template.slug,
                    "name": pipeline_template.name,
                    "description": pipeline_template.description,
                    "input_schema": source_schema,
                    "input_ui_schema": source_ui_schema,
                    "sync_config": None,
                    "is_external_datasource": is_external_datasource,
                    "source": sources.get(source.provider_slug, {}).get(source.slug, {}) if source else {},
                    "transformation": [],
                    "destination": {},
                }
            )

        return DRFResponse(processors)

    def get(self, request, slug):
        data = self.list(request)
        response = None
        for item in data.data:
            if item["slug"] == slug:
                response = item
                break

        return DRFResponse(response) if response else DRFResponse(status=404)


def load_transformations():
    return {}


def load_destinations():
    return {}


class DataSourceEntryViewSet(viewsets.ModelViewSet):
    queryset = DataSourceEntry.objects.all()
    serializer_class = DataSourceEntrySerializer

    def get(self, request, uid=None):
        if uid:
            datasource_entry_object = get_object_or_404(DataSourceEntry, uuid=uuid.UUID(uid))
            if not datasource_entry_object.user_can_read(request.user):
                return DRFResponse(status=404)

            return DRFResponse(
                DataSourceEntrySerializer(instance=datasource_entry_object).data,
            )
        datasources = DataSource.objects.filter(owner=request.user)
        datasource_entries = DataSourceEntry.objects.filter(datasource__in=datasources)
        return DRFResponse(
            DataSourceEntrySerializer(instance=datasource_entries, many=True).data,
        )

    def multiGet(self, request, uids):
        datasource_entries = DataSourceEntry.objects.filter(uuid__in=uids)
        return DRFResponse(
            DataSourceEntrySerializer(instance=datasource_entries, many=True).data,
        )

    def delete(self, request, uid):
        datasource_entry_object = get_object_or_404(DataSourceEntry, uuid=uuid.UUID(uid))
        datasource = datasource_entry_object.datasource

        if datasource_entry_object.datasource.owner != request.user:
            return DRFResponse(status=404)

        try:
            pipeline = datasource_entry_object.datasource.create_data_pipeline()
            pipeline.delete_entry(data=datasource_entry_object.config)
        except Exception as e:
            logger.error(f"Error pipeline data for entry {datasource_entry_object.config}: {e}")

        datasource.size = max(datasource.size - datasource_entry_object.size, 0)
        datasource_entry_object.delete()
        datasource.save()

        return DRFResponse(status=202)

    def text_content(self, request, uid):
        datasource_entry_object = get_object_or_404(DataSourceEntry, uuid=uuid.UUID(uid))
        if not datasource_entry_object.user_can_read(request.user):
            return DRFResponse(status=404)

        pipeline = datasource_entry_object.datasource.create_data_pipeline()
        metadata, content = pipeline.get_entry_text(datasource_entry_object.config)
        return DRFResponse({"content": content, "metadata": metadata})

    def resync(self, request, uid):
        raise NotImplementedError


class DataSourceViewSet(viewsets.ModelViewSet):
    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer

    def get(self, request, uid=None):
        if uid:
            # TODO: return data source entries along with the data source
            return DRFResponse(
                DataSourceSerializer(
                    instance=get_object_or_404(DataSource, uuid=uuid.UUID(uid), owner=request.user),
                ).data,
            )
        return DRFResponse(
            DataSourceSerializer(
                instance=self.queryset.filter(owner=request.user).order_by("-updated_at"), many=True
            ).data,
        )

    def getEntries(self, request, uid):
        datasource = get_object_or_404(DataSource, uuid=uuid.UUID(uid), owner=request.user)
        datasource_entries = DataSourceEntry.objects.filter(datasource=datasource)
        return DRFResponse(
            DataSourceEntrySerializer(instance=datasource_entries, many=True).data,
        )

    def post(self, request):
        owner = request.user
        # Validation for slug
        datasource_type = get_object_or_404(DataSourceType, slug=request.data["type_slug"])
        datasource = DataSource(name=request.data["name"], owner=owner, type=datasource_type)
        datasource_config = datasource.config or {}
        datasource_config["type_slug"] = request.data["type_slug"]
        datasource_config["destination_data"] = request.data.get("destination_data", {})
        datasource_config["transformation_data"] = request.data.get("transformation_data", {})
        datasource.config = datasource_config
        datasource.save()
        return DRFResponse(DataSourceSerializer(instance=datasource).data, status=201)

    def delete(self, request, uid):
        datasource = get_object_or_404(DataSource, uuid=uuid.UUID(uid), owner=request.user)

        # Delete all datasource entries associated with the datasource
        datasource_entries = DataSourceEntry.objects.filter(datasource=datasource)
        for entry in datasource_entries:
            DataSourceEntryViewSet().delete(request=request, uid=str(entry.uuid))

        try:
            pipeline = datasource.create_data_pipeline()
            pipeline.delete_all_entries()
        except Exception as e:
            logger.error(f"Error deleting all entries for datasource {datasource.uuid}: {e}")

        datasource.delete()
        return DRFResponse(status=204)

    def add_entry(self, request, uid):
        datasource = get_object_or_404(DataSource, uuid=uuid.UUID(uid), owner=request.user)

        if datasource and datasource.type.is_external_datasource:
            return DRFResponse({"errors": ["Cannot add entry to external data source"]}, status=400)

        source_data = request.data.get("entry_data", {})

        if not source_data:
            return DRFResponse({"errors": ["No entry_data provided"]}, status=400)

        pipeline = datasource.create_data_pipeline()
        result = pipeline.add_data(source_data_dict=source_data)

        for document_entry in result:
            datasource_entry_name = document_entry.get("name", "Entry")
            datasource_entry_size = (
                document_entry.get("document_size", 0) if document_entry.get("status") == "success" else 0
            )
            DataSourceEntry.objects.create(
                uuid=document_entry.get("id", uuid.uuid4()),
                name=datasource_entry_name,
                datasource=datasource,
                status=(
                    DataSourceEntryStatus.READY
                    if document_entry.get("status") == "success"
                    else DataSourceEntryStatus.FAILED
                ),
                config={
                    "input": {
                        "data": source_data,
                        "name": datasource_entry_name,
                        "size": datasource_entry_size,
                    },
                    "document_ids": document_entry.get("document_ids", []),
                    "document_data": document_entry.get("document_data", {}),
                },
                size=datasource_entry_size,
            )
            datasource.size += datasource_entry_size

        datasource.save()

        return DRFResponse({"status": "success"}, status=200)

    def add_entry_async(self, request, uid):
        # Check if flag_enabled("has_exceeded_storage_quota") is True and deny the request
        if flag_enabled("HAS_EXCEEDED_STORAGE_QUOTA", request=request):
            return DRFResponse("Storage quota exceeded", status=400)

        job = AddDataSourceEntryJob.create(
            func="llmstack.data.tasks.process_datasource_add_entry_request",
            args=[request.user.email, request.data, uid],
        ).add_to_queue()

        return DRFResponse({"job_id": job.id}, status=202)

    def extract_urls(self, request):
        if not request.user.is_authenticated or request.method != "POST":
            return DRFResponse(status=403)

        url = request.data.get("url", None)
        if not url:
            return DRFResponse({"urls": []})

        if not url.startswith("https://") and not url.startswith("http://"):
            url = f"https://{url}"

        job = ExtractURLJob.create(func=extract_urls_task, args=[url]).add_to_queue()

        # Wait for job to finish and return the result
        elapsed_time = 0
        while True and elapsed_time < 30:
            time.sleep(1)

            if isinstance(job, Future) and job.done():
                break
            elif isinstance(job, Job) and (job.is_failed or job.is_finished or job.is_stopped or job.is_canceled):
                break

            elapsed_time += 1

        if isinstance(job, Future):
            urls = job.result()
        elif job.is_failed or job.is_stopped or job.is_canceled:
            urls = [url]
        else:
            urls = job.result

        return DRFResponse({"urls": urls})
