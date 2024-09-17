import datetime
import logging
import uuid

from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response

from llmstack.base.models import Profile
from llmstack.connections.handlers.oauth2_authentication import (
    OAuth2AuthenticationConfiguration,
)
from llmstack.connections.types import (
    ConnectionTypeFactory,
    get_connection_type_interface_subclasses,
)

from .models import Connection, ConnectionType

logger = logging.getLogger(__name__)


class ConnectionsViewSet(viewsets.ViewSet):
    def get_connection_types(self, request):
        connection_type_subclasses = get_connection_type_interface_subclasses()
        data = list(
            map(
                lambda x: {
                    "slug": x.slug(),
                    "provider_slug": x.provider_slug(),
                    "name": x.name(),
                    "description": x.description(),
                    "config_schema": x.get_config_schema(),
                    "config_ui_schema": x.get_config_ui_schema(),
                    "base_connection_type": x.type().value,
                    "metadata": x.metadata(),
                },
                connection_type_subclasses,
            ),
        )

        return Response(data)

    def list(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        if not profile or not profile.connections:
            return Response([])
        connections = []
        for connection_id in profile.connections:
            try:
                connection = ConnectionsViewSet().get(request=request, uid=connection_id).data
                connections.append(connection)
            except Exception:
                logger.exception(f"Error getting connection {connection_id}")
        return Response(connections)

    def get(self, request, uid):
        profile = get_object_or_404(Profile, user=request.user)
        connection = profile.get_connection(uid)
        if not connection:
            return Response(status=404, reason="Connection not found")

        connection_type_handler = ConnectionTypeFactory.get_connection_type_handler(
            connection["connection_type_slug"],
            connection["provider_slug"],
        )()
        connection_obj = connection_type_handler.parse_config(
            connection["configuration"],
        )
        if connection_obj and isinstance(connection_obj, OAuth2AuthenticationConfiguration):
            # This configuration is auto-updated if the token is expired
            if connection_obj.token and connection_obj.expires_at:
                if connection["configuration"]["expires_at"] != connection_obj.expires_at:
                    # We updated the token and expires_at in the connection object
                    connection["configuration"] = connection_obj.model_dump()
                    profile.add_connection(connection)
                    connection = profile.get_connection(uid)

        if connection_obj and hasattr(connection_obj, "expires_in") and connection_obj.expires_in:
            if connection_obj.is_expired:
                refreshed_connection_obj = connection_type_handler.refresh_token(connection_obj)
                if refreshed_connection_obj:
                    connection["configuration"] = refreshed_connection_obj.model_dump()
                    profile.add_connection(connection)
                    connection = profile.get_connection(uid)
                else:
                    connection["status"] = "Failed"
                    profile.add_connection(connection)
                    connection = profile.get_connection(uid)

        return Response(connection)

    def post(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        connection_type_handler = ConnectionTypeFactory.get_connection_type_handler(
            request.data.get("connection_type_slug"),
            request.data.get("provider_slug"),
        )()
        connection_config = connection_type_handler.parse_config(request.data.get("configuration"))
        connection = Connection(
            id=str(uuid.uuid4()),
            name=request.data.get("name"),
            description=request.data.get("description", ""),
            connection_type_slug=request.data.get("connection_type_slug"),
            provider_slug=request.data.get("provider_slug"),
            configuration=connection_config.model_dump(),
            base_connection_type=request.data.get(
                "base_connection_type",
                ConnectionType.BROWSER_LOGIN.value,
            ),
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )
        profile.add_connection(connection.model_dump())

        return Response(connection.model_dump())

    def patch(self, request, uid):
        profile = get_object_or_404(Profile, user=request.user)
        connection_obj = profile.get_connection(uid)
        if not connection_obj:
            return Response(status=404)

        connection = Connection(**connection_obj)
        connection.name = request.data.get("name")
        connection.description = request.data.get("description", "")
        connection.configuration = request.data.get("configuration")
        connection.base_connection_type = request.data.get(
            "base_connection_type",
            ConnectionType.BROWSER_LOGIN.value,
        )
        connection.connection_type_slug = request.data.get(
            "connection_type_slug",
        )
        connection.provider_slug = request.data.get("provider_slug")
        connection.updated_at = datetime.datetime.now().isoformat()
        if "status" in request.data:
            connection.status = request.data.get("status")

        profile.add_connection(connection.model_dump())

        return Response(connection.model_dump())

    def delete(self, request, uid):
        profile = get_object_or_404(Profile, user=request.user)
        if uid not in profile.connections:
            return Response(status=404)

        profile.delete_connection(uid)

        return Response(status=204)
