import logging
from typing import List, Optional

from asgiref.sync import async_to_sync
from langrocks.client import WebBrowser
from langrocks.common.models.web_browser import WebBrowserCommand, WebBrowserCommandType
from pydantic import Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)

logger = logging.getLogger(__name__)


def _query_selector_all(page_html, selector):
    from bs4 import BeautifulSoup

    parser = BeautifulSoup(page_html, "html.parser")
    return parser.select(selector)


class ProfileActivityInput(ApiProcessorSchema):
    profile_url: str = Field(description="The profile URL", default="")
    search_term: str = Field(
        description="The search term to use when looking for a user when profile url is unavailable",
        default="",
    )


class ProfileActivityOutput(ApiProcessorSchema):
    posts: List[str] = Field(
        description="Posts and reposts from the profile",
        default=[],
    )
    comments: List[str] = Field(
        description="Comments made by the user",
        default=[],
    )
    reactions: List[str] = Field(
        description="Reactions to the content",
        default=[],
    )
    profile_url: str = Field(
        description="The profile URL that was used",
        default="",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if something went wrong",
    )


class ProfileActivityConfiguration(ApiProcessorSchema):
    connection_id: str = Field(
        description="LinkedIn login session connection to use",
        json_schema_extra={"advanced_parameter": False, "widget": "connection"},
    )
    n_posts: int = Field(
        description="Number of posts to get",
        default=5,
        ge=1,
        le=100,
    )
    n_comments: int = Field(
        description="Number of comments to get",
        default=5,
        ge=1,
        le=100,
    )
    n_reactions: int = Field(
        description="Number of reactions to get",
        default=5,
        ge=1,
        le=100,
    )


def get_user_recent_posts(profile_url, web_browser):
    profile_url = profile_url.rstrip("/")

    browser_response = web_browser.run_commands(
        [
            WebBrowserCommand(
                command_type=WebBrowserCommandType.GOTO,
                data=f"{profile_url}/recent-activity/all/",
            ),
            WebBrowserCommand(
                command_type=WebBrowserCommandType.WAIT,
                selector="div.feed-shared-update-v2",
                data="5000",
            ),
        ]
    )
    page_html = browser_response.html
    selectors = _query_selector_all(page_html, "div.feed-shared-update-v2")
    text = [selector.text.strip().rstrip() for selector in selectors]

    return text


def get_user_recent_comments(profile_url, web_browser):
    profile_url = profile_url.rstrip("/")

    browser_response = web_browser.run_commands(
        [
            WebBrowserCommand(
                command_type=WebBrowserCommandType.GOTO,
                data=f"{profile_url}/recent-activity/comments/",
            ),
            WebBrowserCommand(
                command_type=WebBrowserCommandType.WAIT,
                selector="div.feed-shared-update-v2",
                data="5000",
            ),
        ]
    )
    page_html = browser_response.html
    selectors = _query_selector_all(page_html, "div.feed-shared-update-v2")
    text = [selector.text.strip().rstrip() for selector in selectors]

    return text


def get_user_recent_reactions(profile_url, web_browser):
    profile_url = profile_url.rstrip("/")
    browser_response = web_browser.run_commands(
        [
            WebBrowserCommand(
                command_type=WebBrowserCommandType.GOTO,
                data=f"{profile_url}/recent-activity/reactions/",
            ),
            WebBrowserCommand(
                command_type=WebBrowserCommandType.WAIT,
                selector="div.feed-shared-update-v2",
                data="5000",
            ),
        ]
    )
    page_html = browser_response.html
    selectors = _query_selector_all(page_html, "div.feed-shared-update-v2")
    text = [selector.text.strip().rstrip() for selector in selectors]

    return text


def get_user_profile_url(search_term, web_browser):
    browser_response = web_browser.run_commands(
        [
            WebBrowserCommand(
                command_type=WebBrowserCommandType.GOTO,
                data=f"https://www.linkedin.com/search/results/people/?keywords={search_term}",
            ),
            WebBrowserCommand(
                command_type=WebBrowserCommandType.WAIT,
                selector="div.search-results-container",
                data="5000",
            ),
        ]
    )
    page_html = browser_response.html

    results = _query_selector_all(page_html, "span.entity-result__title-text a")
    if len(results) > 0 and results[0].has_attr("href"):
        browser_response = web_browser.run_commands(
            [
                WebBrowserCommand(
                    command_type=WebBrowserCommandType.GOTO,
                    data=results[0]["href"],
                ),
                WebBrowserCommand(
                    command_type=WebBrowserCommandType.WAIT,
                    selector="div.body",
                    data="5000",
                ),
            ]
        )
        return browser_response.url

    return None


class ProfileActivityProcessor(
    ApiProcessorInterface[ProfileActivityInput, ProfileActivityOutput, ProfileActivityConfiguration],
):
    @staticmethod
    def name() -> str:
        return "Profile Activity"

    @staticmethod
    def slug() -> str:
        return "profile_activity"

    @staticmethod
    def description() -> str:
        return "Gets the activity of a LinkedIn profile. Searches for the profile if the URL is not provided."

    @staticmethod
    def provider_slug() -> str:
        return "linkedin"

    @classmethod
    def get_output_template(cls) -> Optional[OutputTemplate]:
        return OutputTemplate(
            markdown="""## Posts

{% for post in posts %}
{{post}}

{% endfor %}

## Comments

{% for comment in comments %}
{{comment}}

{% endfor %}

## Reactions

{% for reaction in reactions %}
{{reaction}}

{% endfor %}

{% if error %}
{{error}}
{% endif %}""",
        )

    def process(self) -> dict:
        user_recent_posts = []
        user_recent_comments = []
        user_recent_reactions = []
        user_profile = self._input.profile_url if self._input.profile_url else None

        from django.conf import settings

        output_stream = self._output_stream
        with WebBrowser(
            f"{settings.RUNNER_HOST}:{settings.RUNNER_PORT}",
            interactive=False,
            capture_screenshot=False,
            html=True,
            session_data=(
                self._env["connections"][self._config.connection_id]["configuration"]["_storage_state"]
                if self._config.connection_id
                else ""
            ),
        ) as web_browser:
            if user_profile is None and self._input.search_term:
                user_profile = get_user_profile_url(self._input.search_term, web_browser)
                if not user_profile:
                    async_to_sync(output_stream.write)(
                        ProfileActivityOutput(
                            error=f"No results found for search term {self._input.search_term}",
                        )
                    )

            if user_profile:
                user_recent_posts = get_user_recent_posts(self._input.profile_url, web_browser)
                user_recent_comments = get_user_recent_comments(self._input.profile_url, web_browser)
                user_recent_reactions = get_user_recent_reactions(self._input.profile_url, web_browser)

        async_to_sync(output_stream.write)(
            ProfileActivityOutput(
                posts=user_recent_posts[: self._config.n_posts],
                comments=user_recent_comments[: self._config.n_comments],
                reactions=user_recent_reactions[: self._config.n_reactions],
                profile_url=self._input.profile_url,
            )
        )

        return output_stream.finalize()
