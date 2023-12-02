import datetime
import logging
import uuid

import orjson as json
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response

from llmstack.base.models import Profile
from llmstack.connections.types import (
    ConnectionTypeFactory,
    get_connection_type_interface_subclasses,
)

from .models import Connection, ConnectionType

logger = logging.getLogger(__name__)


class ConnectionsViewSet(viewsets.ViewSet):
    def get_connection_types(self, request):
        connection_type_subclasses = get_connection_type_interface_subclasses()
        data = list(map(lambda x: {
            'slug': x.slug(),
            'provider_slug': x.provider_slug(),
            'name': x.name(),
            'description': x.description(),
            'config_schema': x.get_config_schema(),
            'config_ui_schema': x.get_config_ui_schema(),
            'base_connection_type': x.type().value,
            'metadata': x.metadata(),
        }, connection_type_subclasses))

        return Response(data)

    def list(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        if not profile or not profile.connections:
            return Response([])

        raw_connections = profile.connections.values()
        connections = []

        for connection in raw_connections:
            connection_type_handler = ConnectionTypeFactory.get_connection_type_handler(
                connection['connection_type_slug'], connection['provider_slug'])()
            connection['configuration'] = connection_type_handler.parse_config(
                connection['configuration']).dict()
            connections.append(connection)

        return Response(connections)

    def get(self, request, uid):
        profile = get_object_or_404(Profile, user=request.user)
        connection = profile.get_connection(uid)
        if not connection:
            return Response(status=404, reason='Connection not found')

        connection_type_handler = ConnectionTypeFactory.get_connection_type_handler(
            connection['connection_type_slug'], connection['provider_slug'])()
        connection['configuration'] = connection_type_handler.parse_config(
            connection['configuration']).dict()

        return Response(connection)

    def post(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        connection = Connection(
            id=str(uuid.uuid4()),
            name=request.data.get('name'),
            description=request.data.get('description', ''),
            connection_type_slug=request.data.get('connection_type_slug'),
            provider_slug=request.data.get('provider_slug'),
            configuration=request.data.get('configuration'),
            base_connection_type=request.data.get(
                'base_connection_type', ConnectionType.BROWSER_LOGIN.value),
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )
        profile.add_connection(connection.dict())

        return Response(connection.dict())

    def patch(self, request, uid):
        profile = get_object_or_404(Profile, user=request.user)
        connection_obj = profile.get_connection(uid)
        if not connection_obj:
            return Response(status=404)

        connection = Connection(**connection_obj)
        connection.name = request.data.get('name')
        connection.description = request.data.get('description', '')
        connection.configuration = request.data.get('configuration')
        connection.updated_at = datetime.datetime.now().isoformat()
        if 'status' in request.data:
            connection.status = request.data.get('status')

        profile.add_connection(connection.dict())

        return Response(connection.dict())

    def delete(self, request, uid):
        profile = get_object_or_404(Profile, user=request.user)
        if uid not in profile.connections:
            return Response(status=404)

        profile.delete_connection(uid)

        return Response(status=204)
    
    def get_access_token(self, request, uid):
        profile = get_object_or_404(Profile, user=request.user)
        connection_obj = profile.get_connection(uid)
        if not connection_obj:
            return Response(status=404)
        
        if connection_obj['base_connection_type'] != ConnectionType.OAUTH2.value:
            return Response(status=400, reason='Connection type is not OAUTH2')

        connection = Connection(**connection_obj)
        connection_type_handler = ConnectionTypeFactory.get_connection_type_handler(
            connection.connection_type_slug, connection.provider_slug)()
        connection.configuration = connection_type_handler.parse_config(
            connection.configuration).dict()
        
        new_connection = connection_type_handler.get_access_token(connection)
        profile.add_connection(new_connection.dict())
        
        return Response({'access_token': new_connection.configuration['token']})
                        
