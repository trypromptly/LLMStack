import logging

from django.contrib.auth.models import User

from llmstack.common.utils.utils import retry_on_db_error

logger = logging.getLogger(__name__)


@retry_on_db_error
def process_datasource_add_entry_request(
    user_email,
    request_data,
    datasource_uuid,
):
    from django.contrib.auth.models import User
    from django.test import RequestFactory

    from llmstack.data.apis import DataSourceViewSet

    user = User.objects.get(email=user_email)

    request = RequestFactory().post(
        f"/api/datasources/{datasource_uuid}/add_entry",
        data=request_data,
        format="json",
    )
    request.user = user
    request.data = request_data
    response = DataSourceViewSet().add_entry(request, datasource_uuid)

    return {
        "status_code": response.status_code,
        "data": response.data,
    }


@retry_on_db_error
def process_datasource_entry_resync_request(user_email, entry_uuid):
    from django.contrib.auth.models import User
    from django.test import RequestFactory

    from llmstack.data.apis import DataSourceEntryViewSet

    user = User.objects.get(email=user_email)

    request = RequestFactory().post(
        f"/api/datasource_entries/{entry_uuid}/resync",
        format="json",
    )
    request.user = user
    response = DataSourceEntryViewSet().resync(request, entry_uuid)

    return {
        "status_code": response.status_code,
        "data": response.data,
    }


@retry_on_db_error
def process_datasource_resync_request(user_email, datasource_uuid, **kwargs):
    from django.test import RequestFactory

    from llmstack.data.apis import DataSourceViewSet

    user = User.objects.get(email=user_email)

    request = RequestFactory().post(
        f"/api/datasources/{datasource_uuid}/resync",
        format="json",
    )
    request.user = user
    DataSourceViewSet().resync(request, datasource_uuid)

    return {
        "status_code": 200,
    }
