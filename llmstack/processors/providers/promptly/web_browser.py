from enum import Enum
from typing import List, Optional
from asgiref.sync import async_to_sync
from pydantic import BaseModel, Field
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface, ApiProcessorSchema


class WebBrowserConfiguration(ApiProcessorSchema):
    connection_id: Optional[str] = Field(description='Connection to use', widget='connectionselect')


class BrowserInstructionType(str, Enum):
    CLICK = 'Click'
    TYPE = 'Type'
    WAIT = 'Wait'

    def __str__(self):
        return self.value

class BrowserInstruction(BaseModel):
    type: BrowserInstructionType
    selector: str
    value: Optional[str] = None


class WebBrowserInput(ApiProcessorSchema):
    url: str = Field(..., description='URL to open', required=True)
    instructions: List[BrowserInstruction] = Field(..., description='Instructions to execute', required=True)


class WebBrowserOutput(ApiProcessorSchema):
    text: str = Field(default='', description='Text of the result')


class WebBrowser(ApiProcessorInterface[WebBrowserInput, WebBrowserOutput, WebBrowserConfiguration]):
    """
    Browse a given URL
    """
    @staticmethod
    def name() -> str:
        return 'Web Browser'

    @staticmethod
    def slug() -> str:
        return 'web_browser'

    @staticmethod
    def description() -> str:
        return 'Visit a URL and perform actions'

    @staticmethod
    def provider_slug() -> str:
        return 'promptly'

    def process(self) -> dict:
        output_stream = self._output_stream
        output_text = ''

        # Open playwright browser and navigate to URL
        from playwright.sync_api import sync_playwright
        from django.conf import settings
        with sync_playwright() as p:
            storage_state = self._env['connections'][self._config.connection_id]['configuration']['_storage_state'] if self._config.connection_id else None
            browser = p.chromium.connect(ws_endpoint=settings.PLAYWRIGHT_URL) if hasattr(
                settings, 'PLAYWRIGHT_URL') and settings.PLAYWRIGHT_URL else p.chromium.launch(headless=False)
            context = browser.new_context(storage_state=storage_state)
            page = context.new_page()

            page.goto(self._input.url)

            for instruction in self._input.instructions:
                if instruction.type == BrowserInstructionType.CLICK:
                    page.click(instruction.selector, timeout=5000)
                elif instruction.type == BrowserInstructionType.TYPE:
                    page.type(instruction.selector, instruction.value, timeout=5000)
                elif instruction.type == BrowserInstructionType.WAIT:
                    page.wait_for_selector(instruction.selector, timeout=5000)

                output_text = page.text_content('body')

            context.close()
            browser.close()

        async_to_sync(output_stream.write)(WebBrowserOutput(
            text=output_text
        ))

        output = output_stream.finalize()

        return output
