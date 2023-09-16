import json
import logging
import time
from typing import Any, Dict
from typing import List
from typing import Optional

import markdown
from asgiref.sync import async_to_sync
from bs4 import BeautifulSoup
from bs4 import NavigableString
from pydantic import Field

from common.blocks.http import BearerTokenAuth
from common.blocks.http import HttpAPIProcessor
from common.blocks.http import HttpAPIProcessorInput
from common.blocks.http import HttpMethod
from common.blocks.http import JsonBody
from play.actor import BookKeepingData
from processors.providers.api_processor_interface import ApiProcessorInterface
from processors.providers.api_processor_interface import ApiProcessorSchema

logger = logging.getLogger(__name__)


def traverse_children(element):
    formatted_text = ''

    if isinstance(element, NavigableString):
        return element

    if element.name == 'b' or element.name == 'strong':
        prefix, suffix = '*', '*'
    elif element.name == 'i' or element.name == 'em':
        prefix, suffix = '_', '_'
    else:
        prefix, suffix = '', ''
    for child in element.children:
        formatted_text += traverse_children(child)

    return prefix + formatted_text + suffix


def process_html_element(element):
    if isinstance(element, NavigableString):
        return []

    blocks = []

    if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        block = {
            'type': 'header',
            'text': {
                'type': 'plain_text',
                'text': traverse_children(element),
                'emoji': True,
            },
        }
        blocks.append(block)

    elif element.name == 'p':
        field_blocks = [
            {
                'type': 'mrkdwn',
                'text': traverse_children(element),
            },
        ]
        for child in element.children:
            field_blocks.extend(process_html_element(child))

        section_block = []
        sibling_block = []
        for block in field_blocks:
            if block['type'] in ['image', 'video']:
                sibling_block.append(block)
            else:
                if 'text' in block and block['text']:
                    section_block.append(block)
        block = {
            'type': 'section',
            'fields': section_block,
        }
        if len(block['fields']) > 0:
            blocks.append(block)

        blocks.extend(sibling_block)

    elif element.name in ['ul', 'ol']:
        prefix = '* ' if element.name == 'ul' else '1. '
        for item in element.find_all('li', recursive=False):
            block = {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': prefix + traverse_children(item),
                },
            }
            blocks.append(block)
    elif element.name == 'img':
        block = {
            'type': 'image',
            'image_url': element['src'],
            'alt_text': element.get('alt', ''),
        }
        blocks.append(block)
    elif element.name == 'video':
        block = {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': f"<{element['src']}|Video>",
            },
        }
        blocks.append(block)

    return blocks


def html_to_slack_layout_blocks(html_doc):
    soup = BeautifulSoup(html_doc, 'html.parser')
    body = soup.body
    blocks = []

    for child in body.children:
        blocks.extend(process_html_element(child))
    return blocks


class Attachment(ApiProcessorSchema):
    pretext: str
    text: str


class Block(ApiProcessorSchema):
    type: str
    text: Dict


class Text(ApiProcessorSchema):
    text: str


class SlackPostMessageInput(ApiProcessorSchema):
    slack_user: str
    slack_user_email: str
    token: str
    channel: str
    response_type: str = Field(default='text')
    atachments: Optional[List[Attachment]]
    blocks: Optional[List[Block]]
    text: Optional[str]
    thread_ts: Optional[str]


class SlackPostMessageOutput(ApiProcessorSchema):
    code: int


class SlackPostMessageConfiguration(ApiProcessorSchema):
    pass


class SlackPostMessageProcessor(ApiProcessorInterface[SlackPostMessageInput, SlackPostMessageOutput, SlackPostMessageConfiguration]):
    """
    Slack Post Message API
    """
    @staticmethod
    def name() -> str:
        return 'slack/post_message'

    @staticmethod
    def slug() -> str:
        return 'post_message'

    @staticmethod
    def provider_slug() -> str:
        return 'slack'

    def _send_message(self, message: str, channel: str, thread_ts: str, rich_text: Any, token: str) -> None:
        url = 'https://slack.com/api/chat.postMessage'
        http_processor = HttpAPIProcessor(configuration={'timeout': 60})
        response = http_processor.process(
            HttpAPIProcessorInput(
                url=url,
                method=HttpMethod.POST,
                headers={},
                authorization=BearerTokenAuth(token=self._input.token),
                body=JsonBody(
                    json_body={
                        'channel': channel,
                        'thread_ts': thread_ts,
                        'text': message,
                        'blocks': rich_text,
                    },
                ),
            ).dict(),
        )
        return response
        
        
    def process(self) -> dict:
        _env = self._env
        input = self._input.dict()

        url = 'https://slack.com/api/chat.postMessage'

        try:
            rich_text = json.dumps(
                html_to_slack_layout_blocks(
                    f"<!doctype html><html><body>{markdown.markdown(input['text'])}</body></html>"),
            )
        except Exception as e:
            logger.exception('Error in processing markdown')
            rich_text = ''
            
        self._send_message(input['text'], input['channel'], input['thread_ts'], rich_text, input['token'])
        async_to_sync(self._output_stream.write)(
            SlackPostMessageOutput(code=200),
        )

        return self._output_stream.finalize()

    def on_error(self, error: Any) -> None:
        input = self._input.dict()

        logger.error(f'Error in SlackPostMessageProcessor: {error}')
        error_msg = '\n'.join(error.values()) if isinstance(error, dict) else 'Error in processing request'
        
        self._send_message(error_msg, input['channel'], input['thread_ts'], None, input['token'])
        async_to_sync(self._output_stream.write)(
            SlackPostMessageOutput(code=200),
        )
        self._output_stream.finalize()
        
        return super().on_error(error)
    
    def get_bookkeeping_data(self) -> BookKeepingData:
        return BookKeepingData(input=self._input, timestamp=time.time(), run_data={'slack': {'user': self._input.slack_user, 'user_email': self._input.slack_user_email}})
