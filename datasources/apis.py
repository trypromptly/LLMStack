import logging
import uuid
from urllib.parse import urlparse

from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response as DRFResponse

from .models import DataSource
from .models import DataSourceEntry
from .models import DataSourceEntryStatus
from .models import DataSourceType
from .serializers import DataSourceEntrySerializer
from .serializers import DataSourceSerializer
from .serializers import DataSourceTypeSerializer
from apps.tasks import add_data_entry_task
from apps.tasks import delete_data_entry_task
from apps.tasks import delete_data_source_task
from common.utils.utils import extract_urls_from_sitemap
from common.utils.utils import get_url_content_type
from common.utils.utils import is_sitemap_url
from common.utils.utils import is_youtube_video_url
from common.utils.utils import scrape_url
from datasources.handlers.datasource_type_interface import DataSourceProcessor
from datasources.types import DataSourceTypeFactory
from jobs.adhoc import DataSourceEntryProcessingJob

logger = logging.getLogger(__name__)


class DataSourceTypeViewSet(viewsets.ModelViewSet):
    queryset = DataSourceType.objects.all()
    serializer_class = DataSourceTypeSerializer

    def get(self, request):
        return DRFResponse(DataSourceTypeSerializer(instance=self.queryset, many=True).data)


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

            return DRFResponse(DataSourceEntrySerializer(instance=datasource_entry_object).data)
        datasources = DataSource.objects.filter(owner=request.user)
        datasource_entries = DataSourceEntry.objects.filter(
            datasource__in=datasources,
        )
        return DRFResponse(DataSourceEntrySerializer(instance=datasource_entries, many=True).data)

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
            datasource_type,
        )
        datasource_handler = datasource_handler_cls(
            datasource_entry_object.datasource,
        )
        metadata, content = datasource_handler.get_entry_text(
            datasource_entry_object.config,
        )
        return DRFResponse({'content': content, 'metadata': metadata})


class DataSourceViewSet(viewsets.ModelViewSet):
    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer

    def get(self, request, uid=None):
        if uid:
            # TODO: return data source entries along with the data source
            return DRFResponse(DataSourceSerializer(instance=get_object_or_404(DataSource, uuid=uuid.UUID(uid), owner=request.user)).data)
        return DRFResponse(DataSourceSerializer(instance=self.queryset.filter(owner=request.user).order_by('-updated_at'), many=True).data)

    def getEntries(self, request, uid):
        datasource = get_object_or_404(
            DataSource, uuid=uuid.UUID(uid), owner=request.user,
        )
        datasource_entries = DataSourceEntry.objects.filter(
            datasource=datasource,
        )
        return DRFResponse(DataSourceEntrySerializer(instance=datasource_entries, many=True).data)

    def post(self, request):
        owner = request.user
        datasource_type = get_object_or_404(
            DataSourceType, id=request.data['type'],
        )
        datasource = DataSource.objects.create(
            name=request.data['name'],
            owner=owner,
            type=datasource_type,
        )
        datasource.save()
        return DRFResponse(DataSourceSerializer(instance=datasource).data, status=201)

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

    def add_entry(self, request, uid):
        datasource = get_object_or_404(
            DataSource, uuid=uuid.UUID(uid), owner=request.user,
        )
        entry_data = request.data['entry_data']
        entry_metadata = dict(map(lambda x: (f'md_{x}', request.data['entry_metadata'][x]), request.data['entry_metadata'].keys())) if 'entry_metadata' in request.data else {
        }
        if not entry_data:
            return DRFResponse({'errors': ['No entry_data provided']}, status=400)

        datasource_entry_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
            datasource.type,
        )
        if not datasource_entry_handler_cls:
            logger.error(
                'No handler found for data source type {datasource.type}',
            )
            return DRFResponse({'errors': ['No handler found for data source type']}, status=400)

        datasource_entry_handler: DataSourceProcessor = datasource_entry_handler_cls(
            datasource,
        )

        if not datasource_entry_handler:
            logger.error(
                'Error while creating handler for data source type {datasource.type}',
            )
            return DRFResponse({'errors': ['Error while creating handler for data source type']}, status=400)

        # Validate the entry data against the data source type and add the entry
        datasource_entry_items = datasource_entry_handler.validate_and_process(
            entry_data,
        )

        processed_datasource_entry_items = []
        for datasource_entry_item in datasource_entry_items:
            datasource_entry_object = DataSourceEntry.objects.create(
                datasource=datasource,
                name=datasource_entry_item.name,
                status=DataSourceEntryStatus.PROCESSING,
            )
            datasource_entry_object.save()
            processed_datasource_entry_items.append(
                datasource_entry_item.copy(update={'uuid': str(
                    datasource_entry_object.uuid), 'metadata': entry_metadata}),
            )

        # Trigger a task to process the data source entry
        try:
            job = DataSourceEntryProcessingJob.create(
                func=add_data_entry_task, args=[
                    datasource, processed_datasource_entry_items,
                ],
            ).add_to_queue()
            return DRFResponse({'success': True}, status=202)
        except Exception as e:
            logger.error(f'Error while adding entry to data source: {e}')
            return DRFResponse({'errors': [str(e)]}, status=500)

    def extract_urls(self, request):
        if not request.user.is_authenticated or request.method != 'POST':
            return DRFResponse(status=403)

        url = request.data.get('url', None)
        if not url:
            return DRFResponse({'urls': []})

        if not url.startswith('https://') and not url.startswith('http://'):
            url = f'https://{url}'

        url_content_type = get_url_content_type(url=url)
        url_content_type_parts = url_content_type.split(';')
        mime_type = url_content_type_parts[0]
        if mime_type != 'text/html' or is_youtube_video_url(url):
            return DRFResponse({'urls': [url]})

        # Get url domain
        domain = urlparse(url).netloc
        protocol = urlparse(url).scheme

        if is_sitemap_url(url):
            urls = extract_urls_from_sitemap(url)
            return DRFResponse({'urls': urls})
        else:
            urls = [url]
            try:
                scrapped_url = scrape_url(url)
                hrefs = scrapped_url[0].get('hrefs', [url]) if len(
                    scrapped_url,
                ) > 0 else [url]

                hrefs = list(set(map(lambda x: x.split('?')[0], hrefs)))
                paths = list(filter(lambda x: x.startswith('/'), hrefs))
                fq_urls = list(
                    filter(lambda x: not x.startswith('/'), hrefs),
                )

                urls = [
                    url,
                ] + list(map(lambda entry: f'{protocol}://{domain}{entry}', paths)) + fq_urls

                # Make sure everything is a url
                urls = list(
                    filter(
                        lambda x: x.startswith(
                            'https://',
                        ) or x.startswith('http://'), urls,
                    ),
                )

                # Filter out urls that are not from the same domain
                urls = list(
                    set(filter(lambda x: urlparse(x).netloc == domain, urls)),
                )

            except Exception as e:
                logger.exception(f'Error while extracting urls: {e}')

            return DRFResponse({'urls': urls})
