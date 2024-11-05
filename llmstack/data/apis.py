import json
import logging
import uuid
from datetime import timedelta
from typing import List

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from flags.state import flag_enabled
from langrocks.client import WebBrowser
from rest_framework import viewsets
from rest_framework.response import Response as DRFResponse

from llmstack.base.models import Profile, VectorstoreEmbeddingEndpoint
from llmstack.data.sources.base import DataDocument
from llmstack.data.yaml_loader import (
    get_data_pipeline_template_by_slug,
    get_data_pipelines_from_contrib,
)
from llmstack.jobs.adhoc import AddDataSourceEntryJob
from llmstack.jobs.models import RepeatableJob

from .models import (
    DataSource,
    DataSourceEntry,
    DataSourceEntryStatus,
    DataSourceType,
    DataSourceVisibility,
)
from .serializers import DataSourceEntrySerializer, DataSourceSerializer

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
        from llmstack.data.destinations import (
            PandasStore,
            Pinecone,
            SingleStore,
            Weaviate,
        )

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
                {
                    "slug": PandasStore.slug(),
                    "provider_slug": PandasStore.provider_slug(),
                    "schema": PandasStore.get_schema(),
                    "ui_schema": PandasStore.get_ui_schema(),
                },
            ]
        )

    def transformations(self, request):
        from llmstack.data.transformations import (
            CodeSplitter,
            CSVTextSplitter,
            SemanticDoubleMergingSplitterNodeParser,
            SentenceSplitter,
            UnstructuredIOSplitter,
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
                {
                    "slug": UnstructuredIOSplitter.slug(),
                    "provider_slug": UnstructuredIOSplitter.provider_slug(),
                    "schema": UnstructuredIOSplitter.get_schema(),
                    "ui_schema": UnstructuredIOSplitter.get_ui_schema(),
                },
                {
                    "slug": CSVTextSplitter.slug(),
                    "provider_slug": CSVTextSplitter.provider_slug(),
                    "schema": CSVTextSplitter.get_schema(),
                    "ui_schema": CSVTextSplitter.get_ui_schema(),
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
                DataSourceEntrySerializer(
                    instance=datasource_entry_object, context={"request_user": request.user}
                ).data,
            )
        datasources = DataSource.objects.filter(owner=request.user)
        datasource_entries = DataSourceEntry.objects.filter(datasource__in=datasources)
        return DRFResponse(
            DataSourceEntrySerializer(
                instance=datasource_entries, many=True, context={"request_user": request.user}
            ).data,
        )

    def multiGet(self, request, uids):
        datasource_entries = DataSourceEntry.objects.filter(uuid__in=uids)
        return DRFResponse(
            DataSourceEntrySerializer(
                instance=datasource_entries, many=True, context={"request_user": request.user}
            ).data,
        )

    def delete(self, request, uid):
        datasource_entry_object = get_object_or_404(DataSourceEntry, uuid=uuid.UUID(uid))
        datasource = datasource_entry_object.datasource

        if not datasource.has_write_permission(request.user):
            return DRFResponse(status=403)

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

        node_ids = datasource_entry_object.config.get(
            "document_ids",
            datasource_entry_object.config.get("node_ids", []),
        )
        document = DataDocument(node_ids=node_ids)

        pipeline = datasource_entry_object.datasource.create_data_query_pipeline()
        metadata, content = pipeline.get_entry_text(document=document)
        return DRFResponse({"content": content, "metadata": metadata})

    def create_entry(self, user, document: DataDocument):
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
        return DRFResponse(DataSourceEntrySerializer(instance=entry, context={"request_user": user}).data)

    def process_entry(self, request, uid):
        entry = get_object_or_404(DataSourceEntry, uuid=uuid.UUID(uid))
        if request and request.user != entry.datasource.has_write_permission(request.user):
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

        context = {}
        if request:
            context["request_user"] = request.user
        return DRFResponse(DataSourceEntrySerializer(instance=entry, context=context).data)

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
    serializer_class = DataSourceSerializer

    def get(self, request, uid=None):
        if uid:
            datasource = get_object_or_404(DataSource, uuid=uuid.UUID(uid))
            if not datasource.has_read_permission(request.user):
                return DRFResponse(status=404)

            return DRFResponse(
                DataSourceSerializer(
                    instance=datasource,
                    context={"request_user": request.user},
                ).data,
            )

        datasources = DataSource.objects.filter(owner=request.user).order_by("-updated_at")
        organization = get_object_or_404(Profile, user=request.user).organization

        combined_queryset = datasources

        if organization:
            org_datasources = DataSource.objects.filter(
                owner__in=Profile.objects.filter(organization=organization).values("user"),
                visibility__gte=DataSourceVisibility.ORGANIZATION,
            ).order_by("-updated_at")
            combined_queryset = list(datasources) + list(org_datasources)

        return DRFResponse(
            DataSourceSerializer(
                instance=combined_queryset,
                context={"request_user": request.user},
                many=True,
            ).data,
        )

    def getEntries(self, request, uid):
        datasource = get_object_or_404(DataSource, uuid=uuid.UUID(uid))
        if not datasource.has_read_permission(request.user):
            return DRFResponse(status=404)

        datasource_entries = DataSourceEntry.objects.filter(datasource=datasource)
        return DRFResponse(
            DataSourceEntrySerializer(
                instance=datasource_entries, many=True, context={"request_user": request.user}
            ).data,
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

        if type_slug and type_slug != "custom" and not pipeline_template:
            raise ValueError(f"Pipeline template not found for slug {request.data['type_slug']}")

        if pipeline_template:
            if pipeline_template.pipeline.source is None:
                pipeline_data.pop("source", None)
            if pipeline_template.pipeline.transformations is None:
                pipeline_data.pop("transformations", None)
            if pipeline_template.pipeline.embedding is None:
                pipeline_data.pop("embedding", None)

            # If the request is from a pipeline template, use the pipeline template's embedding coffiguration
            if pipeline_template.pipeline.embedding:
                embedding_data = {"embedding_provider_slug": "openai"}
                if datasource.profile.vectostore_embedding_endpoint == VectorstoreEmbeddingEndpoint.AZURE_OPEN_AI:
                    embedding_data["embedding_provider_slug"] = "azure-openai"
                embedding_transformation = pipeline_template.pipeline.embedding.model_dump()
                embedding_transformation["data"] = embedding_data
                pipeline_data["embedding"] = embedding_transformation

            if pipeline_template.pipeline.destination:
                if (
                    pipeline_template.pipeline.destination.provider_slug == "promptly"
                    and pipeline_template.pipeline.destination.slug == "vector-store"
                ):
                    data_destination_configuration = datasource.profile.get_provider_config(
                        provider_slug="promptly"
                    ).data_destination_configuration

                    pipeline_data["destination"]["data"][
                        "store_provider_slug"
                    ] = data_destination_configuration.provider_slug

                    pipeline_data["destination"]["data"][
                        "store_processor_slug"
                    ] = data_destination_configuration.processor_slug

                    pipeline_data["destination"]["data"][
                        "additional_kwargs"
                    ] = data_destination_configuration.additional_kwargs

        config = {
            "type_slug": request.data["type_slug"],
            "pipeline": pipeline_data,
        }
        datasource.config = config

        datasource.save()
        json_data = DataSourceSerializer(instance=datasource, context={"request_user": request.user}).data
        return DRFResponse(json_data, status=201)

    def patch(self, request, uid):
        datasource = get_object_or_404(DataSource, uuid=uuid.UUID(uid))
        if not datasource.has_write_permission(request.user):
            return DRFResponse(status=403)

        patch_data = request.data
        if "refresh_interval" in patch_data:
            old_job_id = datasource.config.get("refresh_job_id", None)
            if old_job_id:
                # Delete old refresh job if one exists
                try:
                    old_job = RepeatableJob.objects.get(uuid=uuid.UUID(old_job_id))
                    old_job.delete()
                except Exception as e:
                    logger.error(f"Error deleting old refresh job {old_job_id}: {e}")
                datasource.config["refresh_job_id"] = None

            if patch_data["refresh_interval"] in ["Daily", "Weekly"]:
                scheduled_time = timezone.now() + timedelta(minutes=2)
                job_args = {
                    "name": f"Datasource_{datasource.name[:4]}_refresh_job_{datasource.uuid}",
                    "callable": "llmstack.data.tasks.process_datasource_resync_request",
                    "callable_args": json.dumps([request.user.email, str(datasource.uuid)]),
                    "callable_kwargs": json.dumps({}),
                    "enabled": True,
                    "queue": "default",
                    "result_ttl": 86400,
                    "owner": request.user,
                    "scheduled_time": scheduled_time,
                    "task_category": "data_refresh",
                }
                repeat_interval = 7 if patch_data["refresh_interval"] == "Weekly" else 1
                job = RepeatableJob(
                    interval=repeat_interval,
                    interval_unit="days",
                    **job_args,
                )
                job.save()
                datasource.config["refresh_job_id"] = str(job.uuid)
                datasource.config["refresh_interval"] = patch_data["refresh_interval"]
            else:
                datasource.config["refresh_interval"] = None
            datasource.save()

        return DRFResponse(status=204)

    def delete(self, request, uid):
        datasource = get_object_or_404(DataSource, uuid=uuid.UUID(uid))
        if not datasource.has_write_permission(request.user):
            return DRFResponse(status=403)

        # Delete all datasource entries associated with the datasource
        datasource_entries = DataSourceEntry.objects.filter(datasource=datasource)
        for entry in datasource_entries:
            DataSourceEntryViewSet().delete(request=request, uid=str(entry.uuid))

        try:
            pipeline = datasource.create_data_ingestion_pipeline()
            if (
                datasource.config.get("pipeline", {})
                .get("destination", {})
                .get("data", {})
                .get("additional_kwargs", {})
                .get("index_name", None)
                != "text"
            ):
                pipeline.delete_all_entries()
            else:
                logger.info(f"Skipping deletion of all entries for datasource {datasource.uuid}")

        except Exception as e:
            logger.error(f"Error deleting all entries for datasource {datasource.uuid}: {e}")

        refresh_job_id = datasource.config.get("refresh_job_id", None)
        if refresh_job_id:
            try:
                job = RepeatableJob.objects.get(uuid=uuid.UUID(refresh_job_id))
                job.delete()
            except Exception as e:
                logger.error(f"Error deleting refresh job {refresh_job_id}: {e}")

        datasource.delete()
        return DRFResponse(status=204)

    def process_add_entry_request(self, datasource: DataSource, source_data) -> List[DataDocument]:
        source_cls = datasource.pipeline_obj.source_cls
        if not source_cls:
            raise Exception("No source class found for data source")
        source = source_cls(**source_data)
        return source.get_data_documents(datasource_uuid=str(datasource.uuid))

    def add_entry(self, request, uid):
        datasource = get_object_or_404(DataSource, uuid=uuid.UUID(uid))
        if not datasource.has_write_permission(request.user):
            return DRFResponse(status=403)

        if datasource and datasource.type.is_external_datasource:
            return DRFResponse({"errors": ["Cannot add entry to external data source"]}, status=400)

        source_data = request.data.get("source_data", {})

        if not source_data:
            return DRFResponse({"errors": ["No source_data provided"]}, status=400)

        documents = self.process_add_entry_request(datasource, source_data)
        for document in documents:
            create_result = DataSourceEntryViewSet().create_entry(user=request.user, document=document)
            process_result = DataSourceEntryViewSet().process_entry(request=None, uid=str(create_result.data["uuid"]))
            datasource.size += process_result.data["size"]

        datasource.save()

        return DRFResponse(
            DataSourceSerializer(instance=datasource, context={"request_user": request.user}).data, status=200
        )

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
        datasource = get_object_or_404(DataSource, uuid=uuid.UUID(uid))
        if not datasource.has_write_permission(request.user):
            return DRFResponse(status=403)

        entries = DataSourceEntry.objects.filter(datasource=datasource)
        for entry in entries:
            DataSourceEntryViewSet().resync(request, str(entry.uuid))

        return DRFResponse(
            DataSourceSerializer(instance=datasource, context={"request_user": request.user}).data, status=200
        )

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

        runner_url = f"{settings.RUNNER_HOST}:{settings.RUNNER_PORT}"
        urls = [url]

        with WebBrowser(runner_url, html=True, interactive=False, tags_to_extract=["a"]) as browser:
            urls.extend([entry.url for entry in browser.get_links(url=url)])

        urls = list(set(filter(lambda x: x.startswith("http"), urls)))
        return DRFResponse({"urls": urls})
