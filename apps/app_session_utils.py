import logging
from datetime import datetime
from django_redis import get_redis_connection
from django.conf import settings

import orjson as json

APP_SESSION_TIMEOUT = settings.APP_SESSION_TIMEOUT

logger = logging.getLogger(__name__)

app_session_store = get_redis_connection('app_session')
app_session_data_store = get_redis_connection('app_session_data')


def create_app_session(app, app_session_uuid):
    app_session = {
        'uuid': app_session_uuid,
        'app': app.id if app else -1,
        'created_at': str(datetime.now()),
        'last_updated_at': str(datetime.now()),
    }
    app_session_store.set(
        f'app_session_{app_session_uuid}', json.dumps(app_session),
    )
    return app_session


def get_app_session(app_session_uuid):
    app_session = app_session_store.get(f'app_session_{app_session_uuid}')
    if app_session is None:
        return None

    return json.loads(app_session)


def create_app_session_data(app_session, endpoint, data):
    if not app_session:
        return None

    endpoint_id = endpoint['id'] if isinstance(endpoint, dict) else endpoint.id

    app_session_data = {
        'app_session': app_session,
        'endpoint': endpoint_id,
        'data': data,
        'created_at': str(datetime.now()),
        'last_updated_at': str(datetime.now()),
    }
    app_session_data_store.set(
        f'app_session_data_{app_session["uuid"]}_{endpoint_id}', json.dumps(
            app_session_data), APP_SESSION_TIMEOUT,
    )
    return app_session_data


def save_app_session_data(app_session_data):
    app_session_data_store.set(
        f'app_session_data_{app_session_data["app_session"]["uuid"]}_{app_session_data["endpoint"]}', json.dumps(
            app_session_data), APP_SESSION_TIMEOUT,
    )
    return app_session_data


def get_app_session_data(app_session, endpoint):
    if not app_session:
        return None

    endpoint_id = endpoint['id'] if isinstance(endpoint, dict) else endpoint.id

    app_session_data = app_session_data_store.get(
        f'app_session_data_{app_session["uuid"]}_{endpoint_id}',
    )
    if app_session_data is None:
        return None
    return json.loads(app_session_data)
