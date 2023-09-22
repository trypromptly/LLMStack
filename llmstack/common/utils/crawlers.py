import logging
import multiprocessing as mp
from urllib.parse import urlparse

from asgiref.sync import async_to_sync
from playwright.async_api import async_playwright
from scrapy import Selector
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider
from scrapy.spiders import Rule
from scrapy.spiders import SitemapSpider
from unstructured.partition.auto import partition_html
from scrapy.exceptions import CloseSpider

from django.conf import settings

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

    def __init__(self, url, output, max_urls = 20, *args, **kwargs):
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


async def run_playwright(url):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect(ws_endpoint=settings.PLAYWRIGHT_URL) if hasattr(settings, 'PLAYWRIGHT_URL') else await playwright.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_timeout(5000)
        html_content = await page.content()
        await browser.close()
        return html_content


class URLSpider(CrawlSpider):
    name = 'url_spider'

    def __init__(self, url, output, max_depth=0, allowed_domains=None, allowed_regex=None, denied_regex=None, use_renderer=False, *args, **kwargs):
        self.start_urls = [url]
        unstructured_trace = logging.getLogger('unstructured.trace')
        unstructured_trace.disabled = True
        if not allowed_domains:
            self.allowed_domains = [get_domain(url)]
        else:
            self.allowed_domains = allowed_domains.split(',')

        self.rules = (
            Rule(
                LinkExtractor(
                    allow=(allowed_regex or (r'.*')),
                    deny=(denied_regex or (r'.*')),
                ), callback='parse_document',
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

    def get_html_content(self, response):
        if self.use_renderer:
            try:
                html_content = async_to_sync(run_playwright)(response.url)
                return html_content
            except Exception as e:
                logging.exception('Error in fetching file with Playwright')
        return response.body.decode('utf-8')

    def get_text_from_html(self, html_response):
        text_data = [
            text.strip().rstrip() for text in html_response.xpath(
                '//*[not(self::script or self::style)]/text()',
            ).extract()
        ]
        text_data = [text for text in text_data if text != '']
        return '\n'.join(text_data).strip()

    def parse_start_url(self, response):
        data = {}
        data['title'] = response.css('title::text').get()
        data['url'] = response.url

        html_content = self.get_html_content(response)
        if html_content:
            data['raw_text'] = self.get_text_from_html(
                Selector(text=html_content, type='html'),
            )
            data['html_partition'] = '\n\n'.join(
                [str(el) for el in partition_html(text=html_content)],
            )
            data['html_page'] = html_content

            data['hrefs'] = [
                link for link in Selector(text=html_content, type='html').css(
                    'a::attr(href)',
                ).getall()
            ]

        # Add more data extraction here as needed
        self.output.append(data)
        # Follow internal links
        if response.meta.get('depth', 0) < self.max_depth:
            internal_links = data['hrefs']
            for link in internal_links:
                yield response.follow(link, callback=self.parse_document)

    def parse_document(self, response):
        data = {}
        data['title'] = response.css('title::text').get()
        data['url'] = response.url

        html_content = self.get_html_content(response)
        if html_content:
            data['raw_text'] = self.get_text_from_html(
                Selector(text=html_content, type='html'),
            )
            data['html_partition'] = '\n\n'.join(
                [str(el) for el in partition_html(text=html_content)],
            )
            data['html_page'] = html_content

            data['hrefs'] = [
                link for link in Selector(text=html_content, type='html').css(
                    'a::attr(href)',
                ).getall()
            ]

        # Add more data extraction here as needed
        if response.url not in self.start_urls:
            self.output.append(data)

        return dict(
            url=response.url,
            link_text=data['html_partition'],
        )


def _run_url_spider_process(url, q, max_depth=0, allowed_domains=None, allowed_regex=None, denied_regex=None, use_renderer=False):
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
    )
    process.start()  # The script will block here until the crawling is finished
    q.put(output)


def run_url_spider_in_process(url, max_depth=0, allowed_domains=None, allow_regex=None, deny_regex=None, use_renderer=False):
    result = mp.Queue()
    mp.Process(
        target=_run_url_spider_process,
        args=(url, result, max_depth, allowed_domains,
              allow_regex, deny_regex, use_renderer),
    ).start()
    return result.get()
