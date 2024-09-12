import logging
from typing import List, Optional

from asgiref.sync import async_to_sync
from langrocks.client import WebBrowser
from langrocks.common.models.web_browser import WebBrowserCommand, WebBrowserCommandType
from pydantic import BaseModel, Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.utils.text_extraction_service import PromptlyTextExtractionService
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


text_extraction_service = PromptlyTextExtractionService()


class LinkedInProfile(BaseModel):
    about: Optional[str] = Field(
        description="About section",
        default=None,
    )
    experience: Optional[str] = Field(
        description="Experience section",
        default=None,
    )
    education: Optional[str] = Field(
        description="Education section",
        default=None,
    )
    skills: Optional[str] = Field(
        description="Skills section",
        default=None,
    )
    interests: Optional[str] = Field(
        description="Interests section",
        default=None,
    )
    screenshot: Optional[str] = Field(
        description="Screenshot of the profile page",
        default=None,
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
    profile: Optional[LinkedInProfile] = Field(
        description="Profile details",
        default=None,
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
    get_profile_screenshot: bool = Field(
        description="Whether to get a screenshot of the profile",
        default=False,
    )
    get_posts: bool = Field(
        description="Whether to get recent posts",
        default=True,
    )
    get_comments: bool = Field(
        description="Whether to get recent comments",
        default=True,
    )
    get_reactions: bool = Field(
        description="Whether to get recent reactions",
        default=True,
    )


def get_user_profile_details(profile_url, web_browser):
    profile_data = {}

    profile_url = profile_url.rstrip("/")
    browser_response = web_browser.run_commands(
        [
            WebBrowserCommand(
                command_type=WebBrowserCommandType.GOTO,
                data=profile_url,
            ),
            WebBrowserCommand(
                command_type=WebBrowserCommandType.WAIT,
                data="5000",
            ),
        ]
    )
    profile_data["screenshot"] = browser_response.screenshot
    page_html = browser_response.html
    sections = _query_selector_all(page_html, "div#profile-content main section")
    for section in sections:
        card_element = section.select_one(".pv-profile-card__anchor")
        if card_element:
            id = card_element.attrs.get("id")
            if id in ["about", "education", "experience", "skills", "interests"]:
                # Remove all aria-hidden="true" elements in the section
                for aria_hidden in section.select("[aria-hidden=true]"):
                    aria_hidden.decompose()
                extraction_result = text_extraction_service.extract_from_bytes(
                    section.encode(), mime_type="text/html", filename="file.html"
                )
                profile_data[id] = extraction_result.text
    return profile_data


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
    text = [
        text_extraction_service.extract_from_bytes(selector.encode(), mime_type="text/html", filename="file.html").text
        for selector in selectors
    ]

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
    text = [
        text_extraction_service.extract_from_bytes(selector.encode(), mime_type="text/html", filename="file.html").text
        for selector in selectors
    ]

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
    text = [
        text_extraction_service.extract_from_bytes(selector.encode(), mime_type="text/html", filename="file.html").text
        for selector in selectors
    ]

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
            markdown="""Profile URL: {{profile_url}}
{% if profile %}
{{profile.about}}

{{profile.experience}}

{{profile.education}}

{{profile.skills}}

{{profile.interests}}
{% endif %}
{% if posts.size > 0 %}
## Posts

{% for post in posts %}
{{post}}

{% endfor %}
{% endif %}

{% if comments.size > 0 %}
## Comments

{% for comment in comments %}
{{comment}}

{% endfor %}
{% endif %}
{% if reactions.size > 0 %}
## Reactions

{% for reaction in reactions %}
{{reaction}}

{% endfor %}
{% endif %}
{% if error %}
{{error}}
{% endif %}""",
            jsonpath="$.posts",
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
            capture_screenshot=self._config.get_profile_screenshot,
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
                async_to_sync(output_stream.write)(ProfileActivityOutput(profile_url=user_profile))
                profile_details = get_user_profile_details(user_profile, web_browser)
                if profile_details:
                    async_to_sync(output_stream.write)(
                        ProfileActivityOutput(profile=LinkedInProfile(**profile_details))
                    )
                if self._config.get_posts:
                    user_recent_posts = get_user_recent_posts(self._input.profile_url, web_browser)
                    if user_recent_posts:
                        async_to_sync(output_stream.write)(ProfileActivityOutput(posts=user_recent_posts))
                    else:
                        async_to_sync(output_stream.write)(
                            ProfileActivityOutput(
                                error=f"Could not find any posts for the profile {self._input.profile_url}",
                            )
                        )
                if self._config.get_comments:
                    user_recent_comments = get_user_recent_comments(self._input.profile_url, web_browser)
                    if user_recent_comments:
                        async_to_sync(output_stream.write)(ProfileActivityOutput(comments=user_recent_comments))
                    else:
                        async_to_sync(output_stream.write)(
                            ProfileActivityOutput(
                                error=f"Could not find any comments for the profile {self._input.profile_url}",
                            )
                        )
                if self._config.get_reactions:
                    user_recent_reactions = get_user_recent_reactions(self._input.profile_url, web_browser)
                    if user_recent_reactions:
                        async_to_sync(output_stream.write)(ProfileActivityOutput(reactions=user_recent_reactions))
                    else:
                        async_to_sync(output_stream.write)(
                            ProfileActivityOutput(
                                error=f"Could not find any reactions for the profile {self._input.profile_url}",
                            )
                        )

            else:
                async_to_sync(output_stream.write)(
                    ProfileActivityOutput(
                        error="Could not find the profile. Please provide a valid profile URL or search term or check your connection.",
                    )
                )
        return output_stream.finalize()
