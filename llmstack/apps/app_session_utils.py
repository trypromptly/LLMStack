import logging
import uuid
from datetime import datetime, timezone

import orjson as json
from django.conf import settings
from django.core.cache import caches

logger = logging.getLogger(__name__)


def create_app_session(app_session_id=None):
    app_session_store = caches["app_session"]
    app_session_id = app_session_id or str(uuid.uuid4())

    current_time = datetime.now(timezone.utc).isoformat()
    app_session = {
        "id": app_session_id,
        "data": {},
        "created_at": current_time,
        "last_updated_at": current_time,
    }

    app_session_store.set(
        f"app_session_{app_session['id']}",
        json.dumps(app_session),
        settings.APP_SESSION_TIMEOUT,
    )

    return app_session


def get_app_session(app_session_id):
    if not app_session_id:
        return None

    app_session = caches["app_session"].get(f"app_session_{app_session_id}")
    if app_session is None:
        return None

    return json.loads(app_session)


def get_or_create_app_session(app_session_id=None):
    app_session = get_app_session(app_session_id)

    if app_session is None:
        app_session = create_app_session(app_session_id)
    return app_session


def save_app_session_data(app_session_id, key, value):
    app_session = get_or_create_app_session(app_session_id)

    app_session["data"][key] = value
    app_session["last_updated_at"] = datetime.now(timezone.utc).isoformat()

    caches["app_session"].set(
        f"app_session_{app_session['id']}",
        json.dumps(app_session),
        settings.APP_SESSION_TIMEOUT,
    )


def get_app_session_data(app_session_id, key):
    app_session = get_app_session(app_session_id)

    return app_session["data"].get(key, None) if app_session else None


def delete_app_session(app_session_id):
    caches["app_session"].delete(f"app_session_{app_session_id}")
