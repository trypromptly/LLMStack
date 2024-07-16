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


def extract_urls_task(url):
    from urllib.parse import urlparse

    from llmstack.common.utils.utils import (
        extract_urls_from_sitemap,
        get_url_content_type,
        is_sitemap_url,
        is_youtube_video_url,
        scrape_url,
    )

    url_content_type = get_url_content_type(url=url)
    url_content_type_parts = url_content_type.split(";")
    mime_type = url_content_type_parts[0]

    if is_youtube_video_url(url):
        return [url]

    if mime_type != "text/html" and not is_sitemap_url(url):
        return [url]

    # Get url domain
    domain = urlparse(url).netloc
    protocol = urlparse(url).scheme

    if is_sitemap_url(url):
        urls = extract_urls_from_sitemap(url)
        return urls
    else:
        urls = [url]
        try:
            scrapped_url = scrape_url(url)
            hrefs = (
                scrapped_url[0].get("hrefs", [url])
                if len(
                    scrapped_url,
                )
                > 0
                else [url]
            )

            hrefs = list(set(map(lambda x: x.split("?")[0], hrefs)))
            paths = list(filter(lambda x: x.startswith("/"), hrefs))
            fq_urls = list(
                filter(lambda x: not x.startswith("/"), hrefs),
            )

            urls = (
                [
                    url,
                ]
                + list(map(lambda entry: f"{protocol}://{domain}{entry}", paths))
                + fq_urls
            )

            # Make sure everything is a url
            urls = list(
                filter(
                    lambda x: x.startswith(
                        "https://",
                    )
                    or x.startswith("http://"),
                    urls,
                ),
            )

            # Filter out urls that are not from the same domain
            urls = list(
                set(filter(lambda x: urlparse(x).netloc == domain, urls)),
            )

        except Exception as e:
            logger.exception(f"Error while extracting urls: {e}")

        return urls
