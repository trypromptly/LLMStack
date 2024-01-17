import copy
import logging
import re
import time
from enum import Enum
from functools import partial
from typing import List
from urllib.parse import urlparse

import geoip2.database
import requests
from django.conf import settings

from llmstack.common.utils.crawlers import (
    run_sitemap_spider_in_process,
    run_url_spider_in_process,
)

logger = logging.getLogger(__name__)

city_loc_reader = (
    geoip2.database.Reader(
        settings.GEOIP_CITY_DB_PATH,
    )
    if hasattr(
        settings,
        "GEOIP_CITY_DB_PATH",
    )
    else None
)
country_loc_reader = (
    geoip2.database.Reader(
        settings.GEOIP_COUNTRY_DB_PATH,
    )
    if hasattr(
        settings,
        "GEOIP_COUNTRY_DB_PATH",
    )
    else None
)


def get_location(ip):
    if not ip or not city_loc_reader or not country_loc_reader:
        return {}

    try:
        city_loc = city_loc_reader.city(ip)
        country_loc = country_loc_reader.country(ip)
        return {
            "city": city_loc.city.name if city_loc.city.name else city_loc.subdivisions.most_specific.name,
            "country": country_loc.country.name,
            "country_code": country_loc.country.iso_code,
            "continent": country_loc.continent.name,
            "continent_code": country_loc.continent.code,
            "latitude": city_loc.location.latitude,
            "longitude": city_loc.location.longitude,
        }
    except Exception as e:
        logger.exception(e)
        return {}


class MimeType(Enum):
    HTML = "text/html"
    TEXT_XML = "text/xml"
    XML = "application/xml"
    JSON = "application/json"
    TEXT = "text/plain"
    CSS = "text/css"
    JAVASCRIPT = "application/javascript"
    JPEG = "image/jpeg"
    PNG = "image/png"
    GIF = "image/gif"
    SVG = "image/svg+xml"


def is_youtube_video_url(url):
    youtube_regex = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=)?([a-zA-Z0-9_-]{11})"
    match = re.match(youtube_regex, url)
    return match is not None


def extract_urls_from_sitemap(sitemap_xml: str) -> List[str]:
    """
    Extract all URLs from a sitemap.xml file and return them in a list.
    """
    result = scrape_sitemap(sitemap_xml)
    return list(map(lambda entry: entry["url"], result))


def validate_parse_data_uri(
    data_uri,
    data_uri_regex=r"data:(?P<mime>[\w/\-\.]+);name=(?P<filename>.*);base64,(?P<data>.*)",
):
    pattern = re.compile(data_uri_regex)
    match = pattern.match(data_uri)

    if not match:
        raise Exception("Invalid data URI")

    mime_type, file_name, data = match.groups()
    return (mime_type, file_name, data)


def sanitize_dict_values(value):
    if isinstance(value, dict):
        return {k: sanitize_dict_values(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [sanitize_dict_values(v) for v in value]
    elif isinstance(value, str):
        return value.replace('"', r"\"").replace("\\'", "'")
    else:
        return str(value)


def get_key_or_raise(dict, key, exception_message):
    try:
        return dict[key]
    except BaseException:
        raise Exception(exception_message)


def get_domain(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc


def get_url_content_type(url):
    response = requests.head(url, allow_redirects=True, verify=False)

    content_type = response.headers.get("Content-Type", "")
    return content_type


def is_sitemap_url(url):
    try:
        content_type = get_url_content_type(url)
        if (
            "application/xml" in content_type
            or "text/xml" in content_type
            or "text/plain" in content_type
            or "application/rss+xml" in content_type
        ):
            return True
        else:
            return False
    except requests.exceptions.RequestException:
        return False


def scrape_sitemap(sitemap_url):
    if not is_sitemap_url(sitemap_url):
        raise Exception("Invalid sitemap URL")
    return run_sitemap_spider_in_process(sitemap_url)


def scrape_url(url):
    if is_sitemap_url(url):
        return scrape_sitemap(url)
    else:
        return run_url_spider_in_process(url, use_renderer=True)


def _retry_func(
    func,
    exceptions: List[Exception] = [],
    num_tries=1,
    min_delay=1,
    max_delay=None,
    backoff=2,
    log_exception=False,
):
    """
    Retries a function or method until it returns True.
    :param func: The function to be retried.
    :param exceptions: The exceptions to catch. Default is Exception.
    :param num_tries: The number of times to try (not retry) before giving up.
    :param min_delay: The number of seconds to wait before retrying. Default is 0.
    :param max_delay: The maximum number of seconds to wait before retrying. Default is None.
    :param backoff: The backoff multiplier. Default is 2.0.
    """
    min_delay = max(min_delay, 1)
    num_tries = max(num_tries, 1)

    if not max_delay:
        max_delay = min_delay * 2

    _num_tries = num_tries
    _delay = min_delay

    while _num_tries > 0:
        try:
            return func()
        except Exception as e:
            if log_exception and logger:
                logger.exception(e)

            _num_tries -= 1

            if _num_tries == 0:
                raise e
            elif len(exceptions) != 0 and not any([isinstance(e, exception) for exception in exceptions]):
                raise e

            time.sleep(_delay)
            _delay *= backoff
            if max_delay:
                _delay = min(_delay, max_delay)


def retrier(
    exceptions: List[Exception] = [],
    num_tries=1,
    min_delay=1,
    max_delay=None,
    backoff=2,
):
    """
    A decorator for retrying a function or method until it returns True.
    :param exceptions: The exceptions to catch. Default is Exception.
    :param num_tries: The number of times to try (not retry) before giving up.
    :param min_delay: The number of seconds to wait before retrying. Default is 0.
    :param max_delay: The maximum number of seconds to wait before retrying. Default is None.
    :param backoff: The backoff multiplier. Default is 2.0.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            return _retry_func(
                lambda: func(
                    *args,
                    **kwargs,
                ),
                exceptions,
                num_tries,
                min_delay,
                max_delay,
                backoff,
            )

        return wrapper

    return decorator


def retry_func(
    func,
    func_args=None,
    func_kwargs=None,
    exceptions: List[Exception] = [],
    num_tries=1,
    min_delay=1,
    max_delay=None,
    backoff=2,
    log_exception=False,
):
    args = func_args if func_args else []
    kwargs = func_kwargs if func_kwargs else {}
    return _retry_func(
        partial(
            func,
            *args,
            **kwargs,
        ),
        exceptions,
        num_tries,
        min_delay,
        max_delay,
        backoff,
        log_exception,
    )


def get_ui_schema_from_jsonschema(schema):
    ui_schema = {}
    for key in schema.keys():
        if key == "properties":
            ui_schema["ui:order"] = list(schema[key].keys())
            ui_schema[key] = {}
            for prop_key in schema[key].keys():
                ui_schema[key][prop_key] = {}
                if "title" in schema[key][prop_key]:
                    ui_schema[key][prop_key]["ui:label"] = schema[key][prop_key]["title"]
                if "description" in schema[key][prop_key]:
                    ui_schema[key][prop_key]["ui:description"] = schema[key][prop_key]["description"]
                if "type" in schema[key][prop_key]:
                    if schema[key][prop_key]["type"] == "string" and prop_key in (
                        "data",
                        "text",
                        "content",
                    ):
                        ui_schema[key][prop_key]["ui:widget"] = "textarea"
                    elif schema[key][prop_key]["type"] == "string":
                        ui_schema[key][prop_key]["ui:widget"] = "text"
                    elif schema[key][prop_key]["type"] == "integer" or schema[key][prop_key]["type"] == "number":
                        ui_schema[key][prop_key]["ui:widget"] = "updown"
                    elif schema[key][prop_key]["type"] == "boolean":
                        ui_schema[key][prop_key]["ui:widget"] = "checkbox"
                if "enum" in schema[key][prop_key]:
                    ui_schema[key][prop_key]["ui:widget"] = "select"
                    ui_schema[key][prop_key]["ui:options"] = {
                        "enumOptions": [{"value": val, "label": val} for val in schema[key][prop_key]["enum"]],
                    }
                if "widget" in schema[key][prop_key]:
                    ui_schema[key][prop_key]["ui:widget"] = schema[key][prop_key]["widget"]
                if "format" in schema[key][prop_key] and schema[key][prop_key]["format"] == "date-time":
                    ui_schema[key][prop_key]["ui:widget"] = "datetime"
                ui_schema[key][prop_key]["ui:advanced"] = schema[key][prop_key].get(
                    "advanced_parameter",
                    False,
                )
        else:
            ui_schema[key] = copy.deepcopy(schema[key])
    return ui_schema["properties"]
