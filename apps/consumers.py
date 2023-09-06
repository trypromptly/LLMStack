import asyncio
import json
import logging
import uuid

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.http import HttpRequest
from django.http import QueryDict

logger = logging.getLogger(__name__)


@database_sync_to_async
def _build_request_from_input(post_data, scope):
    headers = dict(scope['headers'])
    content_type = headers.get(
        b'content-type', b'application/json',
    ).decode('utf-8')
    path_info = scope.get('path', '')
    method = scope.get('method', '')
    query_string = scope.get('query_string', b'').decode('utf-8')
    query_params = QueryDict(query_string)
    user = scope.get('user')

    http_request = HttpRequest()
    http_request.META = {
        'CONTENT_TYPE': content_type,
        'PATH_INFO': path_info,
        'QUERY_STRING': query_string,
        'HTTP_USER_AGENT': headers.get(b'user-agent', b'').decode('utf-8'),
        'REMOTE_ADDR': headers.get(b'x-forwarded-for', b'').decode('utf-8').split(',')[0].strip(),
        'CONTENT_TYPE': 'application/json',
    }
    http_request.method = method
    http_request.GET = query_params
    http_request.stream = json.dumps(post_data)
    http_request.user = user
    http_request.data = post_data

    return http_request


class AppConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.app_id = self.scope['url_route']['kwargs']['app_id']
        self.preview = True if 'preview' in self.scope['url_route']['kwargs'] else False
        await self.accept()

    async def disconnect(self, close_code):
        # TODO: Close the stream
        pass

    async def _respond_to_event(self, text_data):
        from apps.apis import AppViewSet

        json_data = json.loads(text_data)
        input = json_data.get('input', {})
        event = json_data.get('event', None)
        self._session_id = json_data.get('session_id', None)

        if event == 'run':
            try:
                request_uuid = str(uuid.uuid4())
                request = await _build_request_from_input({'input': input, 'stream': True}, self.scope)
                output_stream = await AppViewSet().run_app_internal_async(self.app_id, self._session_id, request_uuid, request, self.preview)
                async for output in output_stream:
                    if 'errors' in output or 'session' in output:
                        await self.send(text_data=output)
                    else:
                        await self.send(text_data="{\"output\":" + output + '}')

                await self.send(text_data=json.dumps({'event': 'done'}))
            except Exception as e:
                logger.exception(e)
                await self.send(text_data=json.dumps({'errors': [str(e)]}))

        if event == 'stop':
            if self._output_stream is not None:
                self._output_stream.close()

    async def receive(self, text_data):
        loop = asyncio.get_running_loop()
        loop.create_task(
            self._respond_to_event(text_data),
        )
