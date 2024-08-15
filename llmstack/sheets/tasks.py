from llmstack.promptly_sheets.apis import PromptlySheetViewSet


def process_sheet_execute_request(user_email, sheet_id):
    from django.contrib.auth.models import User
    from django.test import RequestFactory

    user = User.objects.get(email=user_email)

    request = RequestFactory().post(
        f"/api/sheets/{sheet_id}/execute",
        format="json",
    )
    request.user = user
    response = PromptlySheetViewSet().execute(request, sheet_uuid=sheet_id)

    return {"status_code": response.status_code, "data": response}
