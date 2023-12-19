import asyncio
import json
import logging
import multiprocessing as mp
import os
from typing import Optional
from urllib.parse import urlparse

import scrapy
from scrapy import Selector, Spider
from scrapy.crawler import CrawlerProcess
from scrapy.exceptions import CloseSpider
from scrapy.http import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule, SitemapSpider
from scrapy_playwright.handler import (
    PERSISTENT_CONTEXT_PATH_KEY,
    BrowserContextWrapper,
    ScrapyPlaywrightDownloadHandler,
)
from twisted.internet.defer import Deferred
from unstructured.partition.auto import partition_html

CRAWLER_SETTINGS = {
    'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'ROBOTSTXT_OBEY': True,
    'LOG_LEVEL': 'ERROR',
}


logger = logging.getLogger(__name__)


def get_domain(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc


class SitemapXMLSpider(SitemapSpider):
    name = 'sitemap_spider'

    def __init__(self, url, output, max_urls=20, *args, **kwargs):
        self.sitemap_urls = [url]
        self.output = output
        self.max_urls = max_urls
        super(SitemapXMLSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        data = {}
        if len(self.output) > self.max_urls:
            raise CloseSpider('Reached maximum number of crawled URLs')

        # Extract data from the page using CSS or XPath selectors
        data['title'] = response.css('title::text').get()
        data['url'] = response.url
        self.output.append(data)


def run_sitemap_spider(sitemap_url):
    output = []
    process = CrawlerProcess(CRAWLER_SETTINGS)
    process.crawl(SitemapXMLSpider, url=sitemap_url, output=output)
    process.start()  # The script will block here until the crawling is finished
    return output


def _run_sitemap_spider_process(sitemap_url, q):
    output = run_sitemap_spider(sitemap_url)
    q.put(output)


def run_sitemap_spider_in_process(sitemap_url):
    result = mp.Queue()
    mp.Process(
        target=_run_sitemap_spider_process,
        args=(sitemap_url, result),
    ).start()
    return result.get()


class PromptlyScrapyPlaywrightDownloadHandler(ScrapyPlaywrightDownloadHandler):
    def __init__(self, settings):
        super().__init__(settings)
        PLAYWRIGHT_URL = f'ws://{os.getenv("RUNNER_HOST", "runner")}:{os.getenv("RUNNER_PLAYWRIGHT_PORT", 50053)}'
        self.browser_cdp_url = PLAYWRIGHT_URL
        logging.getLogger("scrapy-playwright").setLevel(logging.ERROR)

    async def _maybe_connect(self) -> None:
        async with self.browser_launch_lock:
            if not hasattr(self, "browser"):
                logger.info("Connecting using : %s", self.browser_cdp_url)
                self.browser = await self.browser_type.connect(
                    ws_endpoint=self.browser_cdp_url, **self.browser_cdp_kwargs
                )

    async def _create_browser_context(
        self,
        name: str,
        context_kwargs,
        spider=None,
    ):
        """Create a new context, also launching a local browser or connecting
        to a remote one if necessary.
        """
        if hasattr(self, "context_semaphore"):
            await self.context_semaphore.acquire()
        context_kwargs = context_kwargs or {}
        if context_kwargs.get(PERSISTENT_CONTEXT_PATH_KEY):
            context = await self.browser_type.launch_persistent_context(**context_kwargs)
            persistent = True
            remote = False
        elif self.browser_cdp_url and self.browser_cdp_url.startswith("ws"):
            await self._maybe_connect()
            context = await self.browser.new_context(**context_kwargs)
            persistent = False
            remote = True
        elif self.browser_cdp_url:
            await self._maybe_connect_devtools()
            context = await self.browser.new_context(**context_kwargs)
            persistent = False
            remote = True
        else:
            await self._maybe_launch_browser()
            context = await self.browser.new_context(**context_kwargs)
            persistent = False
            remote = False

        context.on(
            "close", self._make_close_browser_context_callback(
                name, persistent, remote, spider)
        )
        self.stats.inc_value("playwright/context_count")
        self.stats.inc_value(
            f"playwright/context_count/persistent/{persistent}")
        self.stats.inc_value(f"playwright/context_count/remote/{remote}")
        logger.debug(
            "Browser context started: '%s' (persistent=%s, remote=%s)",
            name,
            persistent,
            remote,
            extra={
                "spider": spider,
                "context_name": name,
                "persistent": persistent,
                "remote": remote,
            },
        )
        if self.default_navigation_timeout is not None:
            context.set_default_navigation_timeout(
                self.default_navigation_timeout)
        self.context_wrappers[name] = BrowserContextWrapper(
            context=context,
            semaphore=asyncio.Semaphore(value=self.max_pages_per_context),
            persistent=persistent,
        )
        self._set_max_concurrent_context_count()
        return self.context_wrappers[name]

    def download_request(self, request: Request, spider: Spider) -> Deferred:
        return super().download_request(request, spider)


class URLSpider(CrawlSpider):
    name = 'url_spider'

    def __init__(self, url, output, max_depth=0, allowed_domains=None, allowed_regex=None, denied_regex=None, use_renderer=False, connection=None, playwright_url=None, *args, **kwargs):
        self.start_urls = [url]
        unstructured_trace = logging.getLogger('unstructured.trace')
        unstructured_trace.disabled = True
        self.logger.setLevel(logging.ERROR)
        if not allowed_domains:
            self.allowed_domains = [get_domain(url)]
        else:
            self.allowed_domains = allowed_domains.split(',')

        self.playwright_url = playwright_url
        self.rules = (
            Rule(
                LinkExtractor(
                    allow=(allowed_regex or (r'.*')),
                    deny=(denied_regex or (r'.*')),
                ), callback='parse_document'
            ),
        )
        self.custom_settings = {
            'LOG_LEVEL': 'ERROR',
            'EXTENSIONS': {
                'scrapy.extensions.telnet.TelnetConsole': None,  # Disable TelnetConsole extension
            },
        }

        super(URLSpider, self).__init__(*args, **kwargs)
        self.output = output
        self.max_depth = max_depth
        self.use_renderer = use_renderer
        self.connection = connection

    @classmethod
    def update_settings(cls, settings) -> None:
        super().update_settings(settings)
        settings.set('LOG_LEVEL', 'ERROR', priority='spider')
        extensions = settings.getdict('EXTENSIONS')
        settings.set('EXTENSIONS', {
            **extensions,
            'scrapy.extensions.telnet.TelnetConsole': None,
        }, priority='spider')
        download_handler = settings.getdict('DOWNLOAD_HANDLERS')
        settings.set('DOWNLOAD_HANDLERS', {
            **download_handler,
            "http": "llmstack.common.utils.crawlers.PromptlyScrapyPlaywrightDownloadHandler",
            "https": "llmstack.common.utils.crawlers.PromptlyScrapyPlaywrightDownloadHandler",
        }, priority='spider')
        settings.set(
            'TWISTED_REACTOR', "twisted.internet.asyncioreactor.AsyncioSelectorReactor", priority='spider')
        if os.getenv('RUNNER_HOST', None) and os.getenv('RUNNER_PLAYWRIGHT_PORT', None):
            PLAYWRIGHT_URL = f'ws://{os.getenv("RUNNER_HOST", None)}:{os.getenv("RUNNER_PLAYWRIGHT_PORT", None)}'
            settings.set('PLAYWRIGHT_CDP_URL', PLAYWRIGHT_URL)

    def _get_cookies(self, url):
        cookies = []
        if self.connection:
            _storage_state = json.loads(self.connection.get(
                'configuration', {}).get('_storage_state', '{}'))
            cookie_list = _storage_state.get('cookies', {})
            url_domain = '.'.join(urlparse(url).netloc.split('.')[-2:])
            for cookie_entry in cookie_list:
                if cookie_entry.get('domain', None):
                    if cookie_entry['domain'].endswith(url_domain):
                        cookies.append(cookie_entry)
        return cookies

    def start_requests(self):
        if not self.start_urls and hasattr(self, "start_url"):
            raise AttributeError(
                "Crawling could not start: 'start_urls' not found "
                "or empty (but found 'start_url' attribute instead, "
                "did you miss an 's'?)"
            )
        for url in self.start_urls:
            cookies = self._get_cookies(url)
            yield Request(url, meta=dict(playwright=True,
                                         cookies=cookies,
                                         playwright_context_kwargs={
                                             "storage_state": json.loads(self.connection['configuration']['_storage_state']) if self.connection else None
                                         }))

    def get_text_from_html(self, html_response):
        text_data = [
            text.strip().rstrip() for text in html_response.xpath(
                '//*[not(self::script or self::style)]/text()',
            ).extract()
        ]
        text_data = [text for text in text_data if text != '']
        return '\n'.join(text_data).strip()

    def _parse_response_data(self, response):
        html_content = response.body.decode('utf-8')
        page_data = {}
        if html_content:
            page_data = {
                'raw_text': self.get_text_from_html(
                    Selector(text=html_content, type='html'),
                ),
                'html_partition': '\n\n'.join(
                    [str(el) for el in partition_html(text=html_content)],
                ),
                'html_page': html_content,
                'hrefs': [
                    link for link in Selector(text=html_content, type='html').css(
                        'a::attr(href)',
                    ).getall()
                ],
                'videos': [
                    link for link in Selector(text=html_content, type='html').css(
                        'video::attr(src)',
                    ).getall()
                ],
            }

        return {
            'title': response.css('title::text').get(),
            'url': response.url,
            **page_data,
        }

    def parse_start_url(self, response):
        data = self._parse_response_data(response)
        # Add more data extraction here as needed
        self.output.append(data)
        # Follow internal links
        if response.meta.get('depth', 0) < self.max_depth:
            internal_links = data['hrefs']
            for link in internal_links:
                if not get_domain(link) in self.allowed_domains:
                    continue

                req = response.follow(link, callback=self.parse_document)
                cookies = self._get_cookies(link)
                yield req.replace(meta=dict(playwright=True,
                                            playwright_context_kwargs={
                                                "storage_state": json.loads(self.connection['configuration']['_storage_state']) if self.connection else None
                                            },
                                            cookies=cookies))

    def parse_document(self, response):
        data = self._parse_response_data(response)
        self.output.append(data)
        # Add more data extraction here as needed
        if response.url not in self.start_urls:
            self.output.append(data)

        return dict(
            url=response.url,
            link_text=data['html_partition'],
        )


def _run_url_spider_process(url, q, max_depth=0, allowed_domains=None, allowed_regex=None, denied_regex=None, use_renderer=False, connection=None, playwright_url=None):
    output = []
    process = CrawlerProcess(CRAWLER_SETTINGS)
    process.crawl(
        URLSpider,
        url=url, max_depth=max_depth,
        allowed_domains=allowed_domains,
        allowed_regex=allowed_regex,
        denied_regex=denied_regex,
        output=output,
        use_renderer=use_renderer,
        connection=connection,
        playwright_url=playwright_url,
    )
    process.start()  # The script will block here until the crawling is finished
    q.put(output)


def run_url_spider_in_process(url, max_depth=0, allowed_domains=None, allow_regex=None, deny_regex=None, use_renderer=False, connection=None, playwright_url=None):
    result = mp.Queue()
    process = mp.Process(
        target=_run_url_spider_process,
        args=(url, result, max_depth, allowed_domains,
              allow_regex, deny_regex, use_renderer, connection, playwright_url),
    )
    process.start()
    process.join()
    process.close()

    return result.get()
