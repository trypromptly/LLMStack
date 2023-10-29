from llmstack.apps.models import App
from django.test import RequestFactory

from llmstack.apps.apis import AppViewSet


def run_app(app_id=None, input_data=None, *args, **kwargs):
    app = App.objects.get(uuid=app_id)
    user = app.owner
    results = []
    errors = []
    for entry in input_data:
        request_input_data = {'input' : entry, 'stream': False}
        request = RequestFactory().post(f'/api/apps/{app_id}/run', data=request_input_data, format='json')
        request.user = user
        request.data = request_input_data
        response = AppViewSet().run(request=request, uid=app_id)
        if response.status_code == 200:
            results.append(response.data)
            errors.append(None)
        else:
            results.append(None)
            errors.append({
                'code' : response.status_code,
                'detail': response.status_text,
            })
    
    return results, errors

def refresh_datasource(datasource_id=None, datasource_entries=[], *args, **kwargs):
    from llmstack.datasources.apis import DataSourceViewSet
    
    return None, None