from typing import Iterator, Union
from pydantic import Field
from llmstack.connections.models import Connection, ConnectionStatus
from llmstack.connections.types import ConnectionTypeInterface
from .web_login import WebLoginBaseConfiguration


class LinkedInLoginConfiguration(WebLoginBaseConfiguration):
    username: str = Field(description='Username')
    password: str = Field(description='Password', widget='password')


class LinkedInLogin(ConnectionTypeInterface[LinkedInLoginConfiguration]):
    @staticmethod
    def name() -> str:
        return 'LinkedIn Login'

    @staticmethod
    def provider_slug() -> str:
        return 'linkedin'

    @staticmethod
    def slug() -> str:
        return 'web_login'

    @staticmethod
    def description() -> str:
        return 'Login to LinkedIn'

    async def activate(self, connection) -> Iterator[Union[Connection, dict]]:
        # Start playwright browser
        from playwright.async_api import async_playwright
        from django.conf import settings

        async with async_playwright() as p:
            browser = await p.chromium.connect(ws_endpoint=settings.PLAYWRIGHT_URL) if hasattr(
                settings, 'PLAYWRIGHT_URL') and settings.PLAYWRIGHT_URL else await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto('https://www.linkedin.com/login')

            # Login
            await page.fill('input[name="session_key"]', connection.configuration['username'])
            await page.fill('input[name="session_password"]',
                            connection.configuration['password'])
            await page.click('button[type="submit"]')

            # Check if we have errors on the page
            error = await page.query_selector('div[role="alert"]')
            if error:
                error_text = await error.inner_text()
                connection.status = ConnectionStatus.FAILED
                await browser.close()
                yield {'error': error_text, 'connection': connection}
                return

            # Wait for login to complete and redirect to /feed/
            await page.wait_for_url('https://www.linkedin.com/feed/', timeout=5000)

            if page.url != 'https://www.linkedin.com/feed/':
                connection.status = ConnectionStatus.FAILED
                await browser.close()
                yield {'error': 'Login failed', 'connection': connection}
                return

            # Get storage state
            storage_state = await context.storage_state()

            connection.status = ConnectionStatus.ACTIVE
            connection.configuration['_storage_state'] = storage_state

            # Close browser
            await browser.close()

            yield connection
