import logging
import time
import uuid
from concurrent.futures import Future

from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response as DRFResponse
from rq.job import Job

from llmstack.apps.tasks import (
    delete_data_entry_task,
    delete_data_source_task,
    resync_data_entry_task,
)

from .tasks import extract_urls_task

from llmstack.datasources.handlers.datasource_processor import DataSourceEntryItem, DataSourceProcessor
from llmstack.datasources.types import DataSourceTypeFactory
from llmstack.jobs.adhoc import ExtractURLJob
from llmstack.jobs.models import AdhocJob

from .models import DataSource, DataSourceEntry, DataSourceEntryStatus, DataSourceType
from .serializers import (
    DataSourceEntrySerializer,
    DataSourceSerializer,
    DataSourceTypeSerializer,
)

logger = logging.getLogger(__name__)


class DataSourceTypeViewSet(viewsets.ModelViewSet):
    queryset = DataSourceType.objects.all()
    serializer_class = DataSourceTypeSerializer

    def get(self, request):
        return DRFResponse(
            DataSourceTypeSerializer(
                instance=self.queryset,
                many=True).data)


class DataSourceEntryViewSet(viewsets.ModelViewSet):
    queryset = DataSourceEntry.objects.all()
    serializer_class = DataSourceEntrySerializer

    def get(self, request, uid=None):
        if uid:
            datasource_entry_object = get_object_or_404(
                DataSourceEntry, uuid=uuid.UUID(uid),
            )
            if not datasource_entry_object.user_can_read(request.user):
                return DRFResponse(status=404)

            return DRFResponse(
                DataSourceEntrySerializer(
                    instance=datasource_entry_object).data)
        datasources = DataSource.objects.filter(owner=request.user)
        datasource_entries = DataSourceEntry.objects.filter(
            datasource__in=datasources,
        )
        return DRFResponse(
            DataSourceEntrySerializer(
                instance=datasource_entries,
                many=True).data)

    def multiGet(self, request, uids):
        datasource_entries = DataSourceEntry.objects.filter(uuid__in=uids)
        return DRFResponse(
            DataSourceEntrySerializer(
                instance=datasource_entries,
                many=True).data)

    def delete(self, request, uid):
        datasource_entry_object = get_object_or_404(
            DataSourceEntry, uuid=uuid.UUID(uid),
        )
        if datasource_entry_object.datasource.owner != request.user:
            return DRFResponse(status=404)

        delete_data_entry_task(
            datasource_entry_object.datasource, datasource_entry_object,
        )

        return DRFResponse(status=202)

    def text_content(self, request, uid):
        datasource_entry_object = get_object_or_404(
            DataSourceEntry, uuid=uuid.UUID(uid),
        )
        if not datasource_entry_object.user_can_read(request.user):
            return DRFResponse(status=404)

        datasource_type = datasource_entry_object.datasource.type
        datasource_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
            datasource_type, )
        datasource_handler = datasource_handler_cls(
            datasource_entry_object.datasource,
        )
        metadata, content = datasource_handler.get_entry_text(
            datasource_entry_object.config,
        )
        return DRFResponse({'content': content, 'metadata': metadata})

    def resync(self, request, uid):
        datasource_entry_object = get_object_or_404(
            DataSourceEntry, uuid=uuid.UUID(uid),
        )
        if datasource_entry_object.datasource.owner != request.user:
            return DRFResponse(status=404)

        resync_data_entry_task(
            datasource_entry_object.datasource, datasource_entry_object,
        )

        return DRFResponse(status=202)

    def upsert(self, request):
        if 'datasource_id' not in request.data:
            return DRFResponse(
                {'errors': ['No datasource_id provided']}, status=400)

        input_data = request.data.get('input_data')
        if not input_data:
            return DRFResponse(
                {'errors': ['No input_data provided']}, status=400)

        name = input_data['name'] if 'name' in input_data else ''
        data = input_data['data'] if 'data' in input_data else ''
        entry_uuid = input_data['uuid'] if 'uuid' in input_data else None

        if not name or not data:
            return DRFResponse(
                {'errors': ['No name or data provided']}, status=400)

        datasource = get_object_or_404(
            DataSource,
            uuid=request.data['datasource_id'],
            owner=request.user)

        datasource_entry_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
            datasource.type)
        if not datasource_entry_handler_cls:
            logger.error(
                'No handler found for data source type {datasource.type}',
            )
            return DRFResponse(
                {'errors': ['No handler found for data source type']}, status=400)

        datasource_entry_handler = datasource_entry_handler_cls(datasource)
        if not datasource_entry_handler:
            logger.error(
                'Error while creating handler for data source type {datasource.type}', )
            return DRFResponse(
                {'errors': ['Error while creating handler for data source type']}, status=400)

        # Create an entry in the database with status as processing
        if entry_uuid:
            datasource_entry_obj = DataSourceEntry.objects.get(
                uuid=entry_uuid)
        else:
            datasource_entry_obj = DataSourceEntry.objects.create(
                name=name,
                datasource=datasource,
                status=DataSourceEntryStatus.PROCESSING)
            datasource_entry_obj.save()

        try:
            result = datasource_entry_handler.add_entry(
                DataSourceEntryItem(**input_data))
            datasource_entry_config = result.config
            datasource_entry_config["input"] = input_data

            datasource_entry_obj.config = datasource_entry_config
            datasource_entry_obj.size = result.size
            datasource_entry_obj.status = DataSourceEntryStatus.READY
        except Exception as e:
            logger.exception(f'Error adding data_source_entry: %s' %
                             str(input_data['name']))

            datasource_entry_obj.config = {'errors': {'message': str(e)}}
            datasource_entry_obj.status = DataSourceEntryStatus.FAILED

        datasource_entry_obj.save()
        datasource.size += datasource_entry_obj.size
        datasource.save(update_fields=['size'])

        return DRFResponse(
            DataSourceEntrySerializer(
                instance=datasource_entry_obj).data,
            status=200)


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
                        owner=request.user)).data)
        return DRFResponse(
            DataSourceSerializer(
                instance=self.queryset.filter(
                    owner=request.user).order_by('-updated_at'),
                many=True).data)

    def getEntries(self, request, uid):
        datasource = get_object_or_404(
            DataSource, uuid=uuid.UUID(uid), owner=request.user,
        )
        datasource_entries = DataSourceEntry.objects.filter(
            datasource=datasource,
        )
        return DRFResponse(
            DataSourceEntrySerializer(
                instance=datasource_entries,
                many=True).data)

    def post(self, request):
        owner = request.user
        datasource_type = get_object_or_404(
            DataSourceType, id=request.data['type'],
        )

        datasource = DataSource(
            name=request.data['name'],
            owner=owner,
            type=datasource_type,
        )
        # If this is an external data source, then we need to save the config
        # in datasource object
        if datasource_type.is_external_datasource:
            datasource_type_cls = DataSourceTypeFactory.get_datasource_type_handler(
                datasource.type)
            if not datasource_type_cls:
                logger.error(
                    'No handler found for data source type {datasource.type}',
                )
                return DRFResponse(
                    {'errors': ['No handler found for data source type']}, status=400)

            datasource_handler: DataSourceProcessor = datasource_type_cls(
                datasource)
            if not datasource_handler:
                logger.error(
                    f'Error while creating handler for data source {datasource.name}')
                return DRFResponse(
                    {'errors': ['Error while creating handler for data source type']}, status=400)
            config = datasource_type_cls.process_validate_config(
                request.data['config'], datasource)
            datasource.config = config

        datasource.save()
        return DRFResponse(
            DataSourceSerializer(
                instance=datasource).data,
            status=201)

    def put(self, request, uid):
        datasource = get_object_or_404(
            DataSource, uuid=uuid.UUID(uid), owner=request.user,
        )
        if datasource.type.is_external_datasource:
            datasource_type_cls = DataSourceTypeFactory.get_datasource_type_handler(
                datasource.type)
            if not datasource_type_cls:
                logger.error(
                    'No handler found for data source type {datasource.type}',
                )
                return DRFResponse(
                    {'errors': ['No handler found for data source type']}, status=400)

            datasource_handler: DataSourceProcessor = datasource_type_cls(
                datasource)
            if not datasource_handler:
                logger.error(
                    f'Error while creating handler for data source {datasource.name}')
                return DRFResponse(
                    {'errors': ['Error while creating handler for data source type']}, status=400)

            config = datasource_type_cls.process_validate_config(
                request.data['config'], datasource)
            datasource.config = config

            datasource.save()

        return DRFResponse(
            DataSourceSerializer(
                instance=datasource).data,
            status=201)

    def delete(self, request, uid):
        datasource = get_object_or_404(
            DataSource, uuid=uuid.UUID(uid), owner=request.user,
        )

        # Delete all datasource entries associated with the datasource
        datasource_entries = DataSourceEntry.objects.filter(
            datasource=datasource,
        )
        for entry in datasource_entries:
            DataSourceEntryViewSet().delete(request=request, uid=str(entry.uuid))

        # Delete the data from data store
        delete_data_source_task(datasource)

        datasource.delete()
        return DRFResponse(status=204)

    def add_entry_async(self, request, uid):
        datasource = get_object_or_404(
            DataSource, uuid=uuid.UUID(uid), owner=request.user,
        )

        adhoc_job = AdhocJob(
            name=f'add_entry_{datasource.uuid}',
            callable='llmstack.datasources.tasks.process_datasource_add_entry_request',
            callable_args=[
                uid,
                request.data['entry_data']],
            callable_kwargs={},
            queue='default',
            enabled=False,
            repeat=0,
            job_id=None,
            status='queued',
            metadata={
                'datasource_id': uid},
            owner=datasource.owner)

        adhoc_job.save(
            schedule_job=True, func_args=[
                uid, request.data['entry_data']])
        return DRFResponse({'job_id': adhoc_job.uuid}, status=202)

    def add_entry(self, request, uid):
        datasource = get_object_or_404(
            DataSource, uuid=uuid.UUID(uid), owner=request.user,
        )
        if datasource and datasource.type.is_external_datasource:
            return DRFResponse(
                {'errors': ['Cannot add entry to external data source']}, status=400)

        entry_data = request.data['entry_data']
        entry_metadata = dict(
            map(
                lambda x: (
                    f'md_{x}',
                    request.data['entry_metadata'][x]),
                request.data['entry_metadata'].keys())) if 'entry_metadata' in request.data else {}
        if not entry_data:
            return DRFResponse(
                {'errors': ['No entry_data provided']}, status=400)

        datasource_entry_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
            datasource.type, )
        if not datasource_entry_handler_cls:
            logger.error(
                'No handler found for data source type {datasource.type}',
            )
            return DRFResponse(
                {'errors': ['No handler found for data source type']}, status=400)

        datasource_entry_handler: DataSourceProcessor = datasource_entry_handler_cls(
            datasource, )

        if not datasource_entry_handler:
            logger.error(
                'Error while creating handler for data source type {datasource.type}', )
            return DRFResponse(
                {'errors': ['Error while creating handler for data source type']}, status=400)

        # Validate the entry data against the data source type and add the
        # entry
        datasource_entry_items = datasource_entry_handler.validate_and_process(
            entry_data,
        )
        logger.info(f'Adding {len(datasource_entry_items)} entries')
        for datasource_entry_item in datasource_entry_items:
            request.data['datasource_id'] = uid
            request.data['input_data'] = datasource_entry_item.dict()

            response = DataSourceEntryViewSet().upsert(request)
            logger.info(f'Response: {response}')

        return DRFResponse({'status': 'success'}, status=200)

    def extract_urls(self, request):
        if not request.user.is_authenticated or request.method != 'POST':
            return DRFResponse(status=403)

        url = request.data.get('url', None)
        if not url:
            return DRFResponse({'urls': []})

        if not url.startswith('https://') and not url.startswith('http://'):
            url = f'https://{url}'

        logger.info("Staring job to extract urls")

        job = ExtractURLJob.create(
            func=extract_urls_task, args=[
                url
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

        return DRFResponse({'urls': urls})

    def add_entry_jobs(self, request, uid):
        query_params = request.query_params

        jobs = AdhocJob.objects.filter(metadata__datasource_id=uid).order_by(
            '-created_at')

        if 'status' in query_params:
            jobs = jobs.filter(status__in=query_params['status'].split(','))

        return DRFResponse([
            {
                'uuid': str(job.uuid),
                'name': job.name,
                'status': job.status,
                'created_at': job.created_at,
                'updated_at': job.updated_at} for job in jobs], status=200)
