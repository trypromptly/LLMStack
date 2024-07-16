import logging
import time
import uuid
from concurrent.futures import Future

from django.shortcuts import get_object_or_404
from flags.state import flag_enabled
from rest_framework import viewsets
from rest_framework.response import Response as DRFResponse
from rq.job import Job

from llmstack.apps.tasks import resync_data_entry_task
from llmstack.data.datasource_processor import DataPipeline
from llmstack.data.types import DataSourceTypeFactory
from llmstack.data.yaml_loader import get_data_pipelines_from_contrib
from llmstack.jobs.adhoc import ExtractURLJob
from llmstack.jobs.models import AdhocJob

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
            datasource_entry_object = get_object_or_404(
                DataSourceEntry,
                uuid=uuid.UUID(uid),
            )
            if not datasource_entry_object.user_can_read(request.user):
                return DRFResponse(status=404)

            return DRFResponse(
                DataSourceEntrySerializer(
                    instance=datasource_entry_object,
                ).data,
            )
        datasources = DataSource.objects.filter(owner=request.user)
        datasource_entries = DataSourceEntry.objects.filter(
            datasource__in=datasources,
        )
        return DRFResponse(
            DataSourceEntrySerializer(
                instance=datasource_entries,
                many=True,
            ).data,
        )

    def multiGet(self, request, uids):
        datasource_entries = DataSourceEntry.objects.filter(uuid__in=uids)
        return DRFResponse(
            DataSourceEntrySerializer(
                instance=datasource_entries,
                many=True,
            ).data,
        )

    def delete(self, request, uid):
        datasource_entry_object = get_object_or_404(DataSourceEntry, uuid=uuid.UUID(uid))
        datasource = datasource_entry_object.datasource

        if datasource_entry_object.datasource.owner != request.user:
            return DRFResponse(status=404)

        source_data = datasource_entry_object.config.get("input", {}).get("data", {})
        destination_data = request.data.get("destination_data", {})
        if not destination_data and datasource_entry_object.datasource.type_slug in [
            "csv_file",
            "file",
            "pdf",
            "gdrive_file",
            "text",
            "url",
        ]:
            destination_data = datasource_entry_object.datasource.default_destination_request_data

        pipeline = DataPipeline(
            datasource_entry_object.datasource, source_data=source_data, destination_data=destination_data
        )
        pipeline.delete_entry(data=datasource_entry_object.config)
        datasource.size = max(datasource.size - datasource_entry_object.size, 0)
        datasource_entry_object.delete()
        datasource.save()

        return DRFResponse(status=202)

    def text_content(self, request, uid):
        datasource_entry_object = get_object_or_404(DataSourceEntry, uuid=uuid.UUID(uid))
        if not datasource_entry_object.user_can_read(request.user):
            return DRFResponse(status=404)

        source_data = datasource_entry_object.config.get("input", {}).get("data", {})
        destination_data = request.data.get("destination_data", {})
        if not destination_data and datasource_entry_object.datasource.type_slug in [
            "csv_file",
            "file",
            "pdf",
            "gdrive_file",
            "text",
            "url",
        ]:
            destination_data = datasource_entry_object.datasource.default_destination_request_data

        pipeline = DataPipeline(
            datasource_entry_object.datasource, source_data=source_data, destination_data=destination_data
        )
        logger.info(f"Config: {datasource_entry_object.config}")
        metadata, content = pipeline.get_entry_text(datasource_entry_object.config)
        return DRFResponse({"content": content, "metadata": metadata})

    def resync(self, request, uid):
        datasource_entry_object = get_object_or_404(
            DataSourceEntry,
            uuid=uuid.UUID(uid),
        )
        if datasource_entry_object.datasource.owner != request.user:
            return DRFResponse(status=404)

        resync_data_entry_task(
            datasource_entry_object.datasource,
            datasource_entry_object,
        )

        return DRFResponse(status=202)


class DataSourceViewSet(viewsets.ModelViewSet):
    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer

    def get(self, request, uid=None):
        if uid:
            # TODO: return data source entries along with the data source
            return DRFResponse(
                DataSourceSerializer(
                    instance=get_object_or_404(
                        DataSource,
                        uuid=uuid.UUID(uid),
                        owner=request.user,
                    ),
                ).data,
            )
        return DRFResponse(
            DataSourceSerializer(
                instance=self.queryset.filter(
                    owner=request.user,
                ).order_by("-updated_at"),
                many=True,
            ).data,
        )

    def getEntries(self, request, uid):
        datasource = get_object_or_404(
            DataSource,
            uuid=uuid.UUID(uid),
            owner=request.user,
        )
        datasource_entries = DataSourceEntry.objects.filter(
            datasource=datasource,
        )
        return DRFResponse(
            DataSourceEntrySerializer(
                instance=datasource_entries,
                many=True,
            ).data,
        )

    def post(self, request):
        owner = request.user
        # Validation for slug
        datasource_type = get_object_or_404(DataSourceType, slug=request.data["type_slug"])
        datasource = DataSource(name=request.data["name"], owner=owner, type=datasource_type)
        datasource_config = datasource.config or {}
        datasource_config["type_slug"] = request.data["type_slug"]
        datasource.config = datasource_config
        datasource.save()
        return DRFResponse(DataSourceSerializer(instance=datasource).data, status=201)

    def put(self, request, uid):
        datasource = get_object_or_404(
            DataSource,
            uuid=uuid.UUID(uid),
            owner=request.user,
        )
        if datasource.type.is_external_datasource:
            datasource_type_cls = DataSourceTypeFactory.get_datasource_type_handler(
                datasource.type,
            )
            if not datasource_type_cls:
                logger.error(
                    "No handler found for data source type {datasource.type}",
                )
                return DRFResponse(
                    {"errors": ["No handler found for data source type"]},
                    status=400,
                )

            datasource_handler: DataPipeline = datasource_type_cls(
                datasource,
            )
            if not datasource_handler:
                logger.error(
                    f"Error while creating handler for data source {datasource.name}",
                )
                return DRFResponse(
                    {"errors": ["Error while creating handler for data source type"]},
                    status=400,
                )

            config = datasource_type_cls.process_validate_config(
                request.data["config"],
                datasource,
            )
            datasource.config = config

            datasource.save()

        return DRFResponse(
            DataSourceSerializer(
                instance=datasource,
            ).data,
            status=201,
        )

    def delete(self, request, uid):
        datasource = get_object_or_404(DataSource, uuid=uuid.UUID(uid), owner=request.user)

        # Delete all datasource entries associated with the datasource
        datasource_entries = DataSourceEntry.objects.filter(datasource=datasource)
        for entry in datasource_entries:
            DataSourceEntryViewSet().delete(request=request, uid=str(entry.uuid))

        datasource.delete()
        return DRFResponse(status=204)

    def add_entry_async(self, request, uid):
        datasource = get_object_or_404(DataSource, uuid=uuid.UUID(uid), owner=request.user)

        # Check if flag_enabled("has_exceeded_storage_quota") is True and deny the request
        if flag_enabled("HAS_EXCEEDED_STORAGE_QUOTA", request=request):
            return DRFResponse("Storage quota exceeded", status=400)

        adhoc_job = AdhocJob(
            name=f"add_entry_{datasource.uuid}",
            callable="llmstack.data.tasks.process_datasource_add_entry_request",
            callable_args=[
                uid,
                request.data["entry_data"],
            ],
            callable_kwargs={},
            queue="default",
            enabled=False,
            repeat=0,
            job_id=None,
            status="queued",
            metadata={
                "datasource_id": uid,
            },
            owner=datasource.owner,
        )

        adhoc_job.save(
            schedule_job=True,
            func_args=[
                uid,
                request.data["entry_data"],
            ],
        )
        return DRFResponse({"job_id": adhoc_job.uuid}, status=202)

    def add_entry(self, request, uid):
        datasource = get_object_or_404(DataSource, uuid=uuid.UUID(uid), owner=request.user)
        if datasource and datasource.type.is_external_datasource:
            return DRFResponse({"errors": ["Cannot add entry to external data source"]}, status=400)

        entry_data = request.data["entry_data"]
        if not entry_data:
            return DRFResponse({"errors": ["No entry_data provided"]}, status=400)

        source_data = request.data.get("entry_data", {})
        destination_data = request.data.get("destination_data", {})
        if not destination_data and datasource.type_slug in ["csv_file", "file", "pdf", "gdrive_file", "text", "url"]:
            destination_data = datasource.default_destination_request_data

        pipeline = DataPipeline(datasource, source_data=source_data, destination_data=destination_data)
        result = pipeline.run()
        entry_config = {
            "input": {
                "data": entry_data,
                "name": result.get("name", "Entry"),
                "size": result.get("dataprocessed_size", 0),
            },
            "document_ids": result.get("metadata", {}).get("destination", {}).get("document_ids", []),
            "pipeline_data": result,
        }
        if result.get("status_code", 200) != 200:
            DataSourceEntry.objects.create(
                name=result.get("name", "Entry"),
                datasource=datasource,
                status=DataSourceEntryStatus.FAILED,
                config=entry_config,
                size=0,
            )
            datasource.size += 0
        else:
            DataSourceEntry.objects.create(
                name=result.get("name", "Entry"),
                datasource=datasource,
                status=DataSourceEntryStatus.READY,
                config=entry_config,
                size=result.get("dataprocessed_size", 0),
            )
            datasource.size += result.get("dataprocessed_size", 0)

        return DRFResponse({"status": "success"}, status=200)

    def extract_urls(self, request):
        if not request.user.is_authenticated or request.method != "POST":
            return DRFResponse(status=403)

        url = request.data.get("url", None)
        if not url:
            return DRFResponse({"urls": []})

        if not url.startswith("https://") and not url.startswith("http://"):
            url = f"https://{url}"

        logger.info("Staring job to extract urls")

        job = ExtractURLJob.create(
            func=extract_urls_task,
            args=[
                url,
            ],
        ).add_to_queue()

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

    def add_entry_jobs(self, request, uid):
        query_params = request.query_params

        jobs = AdhocJob.objects.filter(metadata__datasource_id=uid).order_by(
            "-created_at",
        )

        if "status" in query_params:
            jobs = jobs.filter(status__in=query_params["status"].split(","))

        return DRFResponse(
            [
                {
                    "uuid": str(job.uuid),
                    "name": job.name,
                    "status": job.status,
                    "created_at": job.created_at,
                    "updated_at": job.updated_at,
                }
                for job in jobs
            ],
            status=200,
        )
