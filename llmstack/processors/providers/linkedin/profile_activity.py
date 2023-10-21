import logging
from asgiref.sync import async_to_sync
from pydantic import Field
from typing import List, Optional
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface, ApiProcessorSchema

logger = logging.getLogger(__name__)


class ProfileActivityInput(ApiProcessorSchema):
    profile_url: str = Field(description='The profile URL', default='')
    search_term: str = Field(
        description='The search term to use when looking for a user when profile url is unavailable', default='')


class ProfileActivityOutput(ApiProcessorSchema):
    posts: List[str] = Field(
        description='Posts and reposts from the profile', default=[])
    comments: List[str] = Field(
        description='Comments made by the user', default=[])
    reactions: List[str] = Field(
        description='Reactions to the content', default=[])
    profile_url: str = Field(
        description='The profile URL that was used', default='')
    error: Optional[str] = Field(
        description='Error message if something went wrong')


class ProfileActivityConfiguration(ApiProcessorSchema):
    connection_id: str = Field(description='LinkedIn login session connection to use',
                               required=True, advanced_parameter=False, widget='connectionselect')
    n_posts: int = Field(description='Number of posts to get',
                         default=5, ge=1, le=100)
    n_comments: int = Field(description='Number of comments to get',
                            default=5, ge=1, le=100)
    n_reactions: int = Field(description='Number of reactions to get',
                             default=5, ge=1, le=100)


class ProfileActivityProcessor(ApiProcessorInterface[ProfileActivityInput, ProfileActivityOutput, ProfileActivityConfiguration]):
    @staticmethod
    def name() -> str:
        return 'Profile Activity'

    @staticmethod
    def slug() -> str:
        return 'profile_activity'

    @staticmethod
    def description() -> str:
        return 'Gets the activity of a LinkedIn profile. Searches for the profile if the URL is not provided.'

    @staticmethod
    def provider_slug() -> str:
        return 'linkedin'

    def process(self) -> dict:
        output_stream = self._output_stream

        from playwright.sync_api import sync_playwright
        from django.conf import settings

        posts = []
        comments = []
        reactions = []
        error = None

        try:
            with sync_playwright() as p:
                storage_state = self._env['connections'][self._config.connection_id]['configuration']['_storage_state']
                browser = p.chromium.connect(ws_endpoint=settings.PLAYWRIGHT_URL) if hasattr(
                    settings, 'PLAYWRIGHT_URL') and settings.PLAYWRIGHT_URL else p.chromium.launch()
                context = browser.new_context(storage_state=storage_state)

                page = context.new_page()

                if self._input.search_term:
                    page.goto(
                        f'https://www.linkedin.com/search/results/people/?keywords={self._input.search_term}')
                    page.wait_for_selector(
                        'div.search-results-container', timeout=5000)
                    results = page.query_selector_all(
                        'span.entity-result__title-text')

                    # Click on the first link, wait for the page to load and get the URL
                    if len(results) > 0:
                        results[0].click()
                    else:
                        raise Exception(
                            f'No results found for search term {self._input.search_term}')

                    page.wait_for_selector('div.body', timeout=5000)
                    self._input.profile_url = page.url

                # Get posts
                page.goto(f'{self._input.profile_url}/recent-activity/all/')
                page.wait_for_selector(
                    'div.feed-shared-update-v2', timeout=5000)
                results = page.query_selector_all(
                    'div.feed-shared-update-v2')
                posts = [result.inner_text() for result in results]

                # Get comments
                page.goto(
                    f'{self._input.profile_url}/recent-activity/comments/')
                page.wait_for_selector(
                    'div.feed-shared-update-v2', timeout=5000)
                results = page.query_selector_all(
                    'div.feed-shared-update-v2')
                comments = [result.inner_text() for result in results]

                # Get reactions
                page.goto(
                    f'{self._input.profile_url}/recent-activity/reactions/')
                page.wait_for_selector(
                    'div.feed-shared-update-v2', timeout=5000)
                results = page.query_selector_all(
                    'div.feed-shared-update-v2')
                reactions = [result.inner_text() for result in results]
        except Exception as e:
            logger.exception(e)
            error = f'Error getting profile activity: {e}'

        async_to_sync(output_stream.write)(
            ProfileActivityOutput(
                posts=posts[:self._config.n_posts],
                comments=comments[:self._config.n_comments],
                reactions=reactions[:self._config.n_reactions],
                profile_url=self._input.profile_url,
                error=error,
            ),
        )

        return output_stream.finalize()
