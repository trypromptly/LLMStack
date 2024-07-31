import logging

logger = logging.getLogger(__name__)


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


def process_datasource_resync_request(user_email, datasource_uuid):
    from django.contrib.auth.models import User
    from django.test import RequestFactory

    from llmstack.data.apis import DataSourceViewSet

    user = User.objects.get(email=user_email)

    request = RequestFactory().post(
        f"/api/datasources/{datasource_uuid}/resync",
        format="json",
    )
    request.user = user
    response = DataSourceViewSet().resync(request, datasource_uuid)

    return {
        "status_code": response.status_code,
        "data": response.data,
    }


def extract_page_hrefs_task(page_url, cdp_url=None):
    from playwright.sync_api import sync_playwright

    if not page_url.startswith("https://") and not page_url.startswith("http://"):
        page_url = f"https://{page_url}"

    urls = [page_url]
    try:
        with sync_playwright() as p:
            if not cdp_url:
                from django.conf import settings

                cdp_url = settings.PLAYWRIGHT_URL

            browser = p.chromium.connect(ws_endpoint=cdp_url)
            context = browser.new_context()
            page = context.new_page()
            page.goto(page_url, timeout=2000)
            # Extract all URLs from the page
            anchors = page.query_selector_all("a")
            for anchor in anchors:
                href = anchor.get_attribute("href")
                if href and href.startswith("http"):
                    urls.append(href)

            browser.close()
    except Exception:
        logger.exception("Error while extracting page hrefs")
    return list(set(urls))
