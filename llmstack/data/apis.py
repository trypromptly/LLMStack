import logging
import time
import uuid
from concurrent.futures import Future
from typing import List

from django.shortcuts import get_object_or_404
from flags.state import flag_enabled
from rest_framework import viewsets
from rest_framework.response import Response as DRFResponse
from rq.job import Job

from llmstack.data.schemas import DataDocument
from llmstack.data.yaml_loader import (
    get_data_pipeline_template_by_slug,
    get_data_pipelines_from_contrib,
)
from llmstack.jobs.adhoc import AddDataSourceEntryJob, ExtractURLJob

from .models import DataSource, DataSourceEntry, DataSourceEntryStatus, DataSourceType
from .serializers import DataSourceEntrySerializer, DataSourceSerializer
from .tasks import extract_page_hrefs_task

logger = logging.getLogger(__name__)


class DataSourceTypeViewSet(viewsets.ViewSet):
    def list(self, request):
        processors = []

        pipeline_templates = get_data_pipelines_from_contrib()

        for pipeline_template in pipeline_templates:
            processors.append(
                {
                    **pipeline_template.default_dict(),
                    "sync_config": None,
                    "is_external_datasource": not pipeline_template.pipeline.source,
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


class PipelineViewSet(viewsets.ViewSet):
    def templates(self, request):
        templates_data = []
        pipeline_templates = get_data_pipelines_from_contrib()
        for pipeline_template in pipeline_templates:
            templates_data.append(
                {
                    **pipeline_template.default_dict(),
                    "is_external_datasource": not pipeline_template.pipeline.source,
                }
            )
        return DRFResponse(templates_data)

    def sources(self, request):
        from llmstack.data.sources import FileSchema, TextSchema, URLSchema

        return DRFResponse(
            [
                {
                    "slug": FileSchema.slug(),
                    "provider_slug": FileSchema.provider_slug(),
                    "schema": FileSchema.get_schema(),
                    "ui_schema": FileSchema.get_ui_schema(),
                },
                {
                    "slug": TextSchema.slug(),
                    "provider_slug": TextSchema.provider_slug(),
                    "schema": TextSchema.get_schema(),
                    "ui_schema": TextSchema.get_ui_schema(),
                },
                {
                    "slug": URLSchema.slug(),
                    "provider_slug": URLSchema.provider_slug(),
                    "schema": URLSchema.get_schema(),
                    "ui_schema": URLSchema.get_ui_schema(),
                },
            ]
        )

    def destinations(self, request):
        from llmstack.data.destinations import Pinecone, SingleStore, Weaviate

        return DRFResponse(
            [
                {
                    "slug": Weaviate.slug(),
                    "provider_slug": Weaviate.provider_slug(),
                    "schema": Weaviate.get_schema(),
                    "ui_schema": Weaviate.get_ui_schema(),
                },
                {
                    "slug": SingleStore.slug(),
                    "provider_slug": SingleStore.provider_slug(),
                    "schema": SingleStore.get_schema(),
                    "ui_schema": SingleStore.get_ui_schema(),
                },
                {
                    "slug": Pinecone.slug(),
                    "provider_slug": Pinecone.provider_slug(),
                    "schema": Pinecone.get_schema(),
                    "ui_schema": Pinecone.get_ui_schema(),
                },
            ]
        )

    def transformations(self, request):
        from llmstack.data.transformations import (
            CodeSplitter,
            SemanticDoubleMergingSplitterNodeParser,
            SentenceSplitter,
        )

        return DRFResponse(
            [
                {
                    "slug": CodeSplitter.slug(),
                    "provider_slug": CodeSplitter.provider_slug(),
                    "schema": CodeSplitter.get_schema(),
                    "ui_schema": CodeSplitter.get_ui_schema(),
                },
                {
                    "slug": SemanticDoubleMergingSplitterNodeParser.slug(),
                    "provider_slug": SemanticDoubleMergingSplitterNodeParser.provider_slug(),
                    "schema": SemanticDoubleMergingSplitterNodeParser.get_schema(),
                    "ui_schema": SemanticDoubleMergingSplitterNodeParser.get_ui_schema(),
                },
                {
                    "slug": SentenceSplitter.slug(),
                    "provider_slug": SentenceSplitter.provider_slug(),
                    "schema": SentenceSplitter.get_schema(),
                    "ui_schema": SentenceSplitter.get_ui_schema(),
                },
            ]
        )

    def embeddings(self, request):
        from llmstack.data.transformations import EmbeddingsGenerator

        return DRFResponse(
            [
                {
                    "slug": EmbeddingsGenerator.slug(),
                    "provider_slug": EmbeddingsGenerator.provider_slug(),
                    "schema": EmbeddingsGenerator.get_schema(),
                    "ui_schema": EmbeddingsGenerator.get_ui_schema(),
                }
            ]
        )


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

        node_ids = datasource_entry_object.config.get(
            "document_ids",
            datasource_entry_object.config.get("nodes", datasource_entry_object.config.get("node_ids", [])),
        )
        document = DataDocument(node_ids=node_ids)

        pipeline = datasource_entry_object.datasource.create_data_ingestion_pipeline()
        pipeline.delete_entry(document)

        datasource.size = max(datasource.size - datasource_entry_object.size, 0)
        datasource_entry_object.delete()
        datasource.save()

        return DRFResponse(status=202)

    def text_content(self, request, uid):
        datasource_entry_object = get_object_or_404(DataSourceEntry, uuid=uuid.UUID(uid))
        if not datasource_entry_object.user_can_read(request.user):
            return DRFResponse(status=404)

        pipeline = datasource_entry_object.datasource.create_data_query_pipeline()
        metadata, content = pipeline.get_entry_text(datasource_entry_object.config)
        return DRFResponse({"content": content, "metadata": metadata})

    def create_entry(self, document: DataDocument):
        datasource = get_object_or_404(DataSource, uuid=document.datasource_uuid)

        entry = DataSourceEntry.objects.create(
            uuid=document.id_,
            name=document.name,
            datasource=datasource,
            status=DataSourceEntryStatus.PROCESSING,
            config={
                **document.model_dump(
                    include=[
                        "name",
                        "text_objref",
                        "content",
                        "mimetype",
                        "metadata",
                        "extra_info",
                        "processing_errors",
                        "request_data",
                        "datasource_uuid",
                        "node_ids",
                    ]
                ),
            },
            size=0,
        )
        return DRFResponse(DataSourceEntrySerializer(instance=entry).data)

    def process_entry(self, request, uid):
        entry = get_object_or_404(DataSourceEntry, uuid=uuid.UUID(uid))
        if request and request.user != entry.datasource.owner:
            return DRFResponse(status=404)

        document = DataDocument(**entry.config)
        pipeline_obj = entry.datasource.create_data_ingestion_pipeline()
        try:
            document = pipeline_obj.process(document)
            entry.config = {
                **document.model_dump(
                    include=[
                        "name",
                        "text_objref",
                        "content",
                        "mimetype",
                        "metadata",
                        "extra_info",
                        "processing_errors",
                        "request_data",
                        "datasource_uuid",
                        "node_ids",
                    ]
                ),
            }
            entry.size = len(document.node_ids) * 1536
        except Exception as e:
            document.processing_errors = [str(e)]

        entry.status = DataSourceEntryStatus.READY if not document.processing_errors else DataSourceEntryStatus.FAILED
        entry.save(update_fields=["config", "size", "status", "updated_at"])

        return DRFResponse(DataSourceEntrySerializer(instance=entry).data)

    def resync(self, request, uid):
        datasource_entry_object = get_object_or_404(DataSourceEntry, uuid=uuid.UUID(uid))

        if datasource_entry_object.datasource.owner != request.user:
            return DRFResponse(status=404)

        old_size = datasource_entry_object.size

        entry_config = {**datasource_entry_object.config}
        document = DataDocument(**entry_config)

        pipeline = datasource_entry_object.datasource.create_data_ingestion_pipeline()

        pipeline.delete_entry(document=document)
        result = self.process_entry(request, uid)

        new_size = result.data["size"]
        datasource_entry_object.datasource.size = max(datasource_entry_object.datasource.size - old_size + new_size, 0)
        datasource_entry_object.datasource.save()

        return self.process_entry(request, uid)

    def resync_async(self, request, uid):
        job = AddDataSourceEntryJob.create(
            func="llmstack.data.tasks.process_datasource_entry_resync_request",
            args=[request.user.email, uid],
        ).add_to_queue()

        return DRFResponse({"job_id": job.id}, status=202)


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
        pipeline_data = request.data.get("pipeline", None)
        name = request.data.get("name", None)
        type_slug = request.data.get("type_slug", None)
        # Validation for slug
        datasource_type = get_object_or_404(DataSourceType, slug="text")

        datasource = DataSource(name=name, owner=owner, type=datasource_type)

        pipeline_template = get_data_pipeline_template_by_slug(type_slug)

        if type_slug and not pipeline_template:
            raise ValueError(f"Pipeline template not found for slug {request.data['type_slug']}")

        if pipeline_template:
            # If the request is from a pipeline template, use the pipeline template's embedding coffiguration
            if pipeline_template.pipeline.embedding:
                embedding_data = {"embedding_provider_slug": "openai"}
                if datasource.profile.vectostore_embedding_endpoint == "azure_openai":
                    embedding_data["embedding_provider_slug"] = "azure-openai"
                embedding_transformation = pipeline_template.pipeline.embedding.model_dump()
                embedding_transformation["data"] = embedding_data
                pipeline_data["embedding"] = embedding_transformation

            if pipeline_template.pipeline.destination:
                if (
                    pipeline_template.pipeline.destination.provider_slug == "promptly"
                    and pipeline_template.pipeline.destination.slug == "vector-store"
                ):
                    store_provider_slug = datasource.profile.get_provider_config(
                        provider_slug="promptly"
                    ).data_destination_configuration.provider_slug
                    pipeline_data["destination"]["data"]["store_provider_slug"] = store_provider_slug

        config = {
            "type_slug": request.data["type_slug"],
            "pipeline": pipeline_data,
        }
        datasource.config = config

        datasource.save()
        json_data = DataSourceSerializer(instance=datasource).data
        return DRFResponse(json_data, status=201)

    def delete(self, request, uid):
        datasource = get_object_or_404(DataSource, uuid=uuid.UUID(uid), owner=request.user)

        # Delete all datasource entries associated with the datasource
        datasource_entries = DataSourceEntry.objects.filter(datasource=datasource)
        for entry in datasource_entries:
            DataSourceEntryViewSet().delete(request=request, uid=str(entry.uuid))

        try:
            pipeline = datasource.create_data_ingestion_pipeline()
            pipeline.delete_all_entries()
        except Exception as e:
            logger.error(f"Error deleting all entries for datasource {datasource.uuid}: {e}")

        datasource.delete()
        return DRFResponse(status=204)

    def process_add_entry_request(self, datasource: DataSource, source_data) -> List[DataDocument]:
        source_cls = datasource.pipeline_obj.source_cls
        if not source_cls:
            raise Exception("No source class found for data source")
        source = source_cls(**source_data)
        return source.get_data_documents(datasource_uuid=str(datasource.uuid))

    def add_entry(self, request, uid):
        datasource = get_object_or_404(DataSource, uuid=uuid.UUID(uid), owner=request.user)

        if datasource and datasource.type.is_external_datasource:
            return DRFResponse({"errors": ["Cannot add entry to external data source"]}, status=400)

        source_data = request.data.get("source_data", {})

        if not source_data:
            return DRFResponse({"errors": ["No source_data provided"]}, status=400)

        documents = self.process_add_entry_request(datasource, source_data)
        for document in documents:
            create_result = DataSourceEntryViewSet().create_entry(document=document)
            process_result = DataSourceEntryViewSet().process_entry(request=None, uid=str(create_result.data["uuid"]))
            datasource.size += process_result.data["size"]

        datasource.save()

        return DRFResponse(DataSourceSerializer(instance=datasource).data, status=200)

    def add_entry_async(self, request, uid):
        # Check if flag_enabled("has_exceeded_storage_quota") is True and deny the request
        if flag_enabled("HAS_EXCEEDED_STORAGE_QUOTA", request=request):
            return DRFResponse("Storage quota exceeded", status=400)

        job = AddDataSourceEntryJob.create(
            func="llmstack.data.tasks.process_datasource_add_entry_request",
            args=[request.user.email, request.data, uid],
        ).add_to_queue()

        return DRFResponse({"job_id": job.id}, status=202)

    def resync(self, request, uid):
        datasource = get_object_or_404(DataSource, uuid=uuid.UUID(uid), owner=request.user)

        entries = DataSourceEntry.objects.filter(datasource=datasource)
        for entry in entries:
            DataSourceEntryViewSet().resync(request, str(entry.uuid))

        return DRFResponse(DataSourceSerializer(instance=datasource).data, status=200)

    def resync_async(self, request, uid):
        job = AddDataSourceEntryJob.create(
            func="llmstack.data.tasks.process_datasource_resync_request",
            args=[request.user.email, uid],
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

        job = ExtractURLJob.create(func=extract_page_hrefs_task, args=[url]).add_to_queue()

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
