import base64
import imaplib
import logging
from datetime import date
from email.parser import BytesParser
from email.policy import default
from typing import List, Literal, Optional, Union

from asgiref.sync import async_to_sync
from pydantic import BaseModel, Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.common.blocks.base.processor import Schema
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface

logger = logging.getLogger(__name__)


class GmailEmailProvider(BaseModel):
    type: Literal["gmail"] = "gmail"


class OutlookEmailProvider(BaseModel):
    type: Literal["outlook"] = "outlook"


class YahooEmailProvider(BaseModel):
    type: Literal["yahoo"] = "yahoo"


EmailProvider = Union[GmailEmailProvider, OutlookEmailProvider, YahooEmailProvider]


class EmailSearchInput(Schema):
    sender: Optional[str] = Field(None, description="Filter by email sender")
    subject: Optional[str] = Field(None, description="Filter by email subject")
    since: Optional[date] = Field(
        None, description="Filter emails since a specific date", json_schema_extra={"widget": "date"}
    )
    before: Optional[date] = Field(
        None, description="Filter emails before a specific date", json_schema_extra={"widget": "date"}
    )
    unseen: bool = Field(False, description="Filter for unread emails")
    seen: bool = Field(False, description="Filter for read emails")

    def build_search_query(self) -> str:
        """Build the IMAP search query based on the provided filters."""
        query_parts = []

        if self.sender:
            query_parts.append(f'FROM "{self.sender}"')

        if self.subject:
            query_parts.append(f'SUBJECT "{self.subject}"')

        if self.since:
            query_parts.append(f'SINCE "{self.since.strftime("%d-%b-%Y")}"')

        if self.before:
            query_parts.append(f'BEFORE "{self.before.strftime("%d-%b-%Y")}"')

        if self.unseen:
            query_parts.append("UNSEEN")

        if self.seen:
            query_parts.append("SEEN")

        # Join all parts with a space to form the final search query
        return " ".join(query_parts)


class EmailSearchConfigurations(Schema):
    email_provider: EmailProvider = Field(
        default=GmailEmailProvider(),
        description="Email provider to use",
        json_schema_extra={"advanced_parameter": False},
    )
    connection_id: Optional[str] = Field(
        default=None,
        json_schema_extra={"widget": "connection", "advanced_parameter": False},
        description="Use your authenticated connection to make the request",
    )
    mailbox: str = Field(
        default="INBOX",
        description="Mailbox to search in",
    )


class EmailSearchResult(Schema):
    id: str = Field(default="", description="Email ID")
    subject: str = Field(description="Subject of the email")
    sender: str = Field(description="Sender of the email")
    body: Optional[str] = Field(default=None, description="Body of the email")
    text_body: Optional[str] = Field(default=None, description="Text body of the email")
    html_body: Optional[str] = Field(default=None, description="HTML body of the email")
    html_body_text: Optional[str] = Field(default=None, description="HTML body of the email as text")
    attachments: Optional[List[str]] = Field(default=[], description="Email Attachments")
    cc: Optional[List[str]] = Field(default=[], description="CC of the email")
    bcc: Optional[List[str]] = Field(default=[], description="BCC of the email")


class EmailSearchOutput(Schema):
    results: List[EmailSearchResult] = Field(
        default=[],
        description="Email search results",
    )


class EmailSenderProcessor(ApiProcessorInterface[EmailSearchInput, EmailSearchOutput, EmailSearchConfigurations]):
    @staticmethod
    def name() -> str:
        return "Email Search"

    @staticmethod
    def slug() -> str:
        return "email_search"

    @staticmethod
    def description() -> str:
        return "Search for emails"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    @classmethod
    def get_output_template(cls) -> OutputTemplate | None:
        return OutputTemplate(
            markdown="""{% for result in results %}
{{result.subject}}
{{result.body}}

{% endfor %}""",
            jsonpath="$.results",
        )

    def process(self) -> dict:
        # Connect to the email server
        mail = None
        connection = self._env["connections"][self._config.connection_id]["configuration"]
        if isinstance(self._config.email_provider, GmailEmailProvider):
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(connection["username"], connection["password"])
        elif isinstance(self._config.email_provider, OutlookEmailProvider):
            mail = imaplib.IMAP4_SSL("imap-mail.outlook.com")
            mail.login(connection["username"], connection["password"])
        elif isinstance(self._config.email_provider, YahooEmailProvider):
            mail = imaplib.IMAP4_SSL("imap.mail.yahoo.com")
            mail.login(connection["username"], connection["password"])
        else:
            raise ValueError("Invalid email provider")

        mail.select(mailbox=self._config.mailbox)
        status, messages = mail.search(None, self._input.build_search_query())
        ids = messages[0].split()
        results = []
        for id in ids:
            status, msg_data = mail.fetch(id, "(BODY.PEEK[])")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = BytesParser(policy=default).parsebytes(response_part[1])
                    email_data = EmailSearchResult(
                        id=id.decode("utf-8"),
                        subject=msg["subject"],
                        sender=msg["from"],
                    )
                    email_data.cc = list(map(str, msg["cc"].addresses)) if "cc" in msg else []
                    email_data.bcc = list(map(str, msg["bcc"].addresses)) if "bcc" in msg else []
                    if msg.is_multipart():
                        for part in msg.iter_parts():
                            if part.get_content_type() == "text/plain":
                                email_data.text_body = part.get_payload(decode=True).decode(part.get_content_charset())
                            elif part.get_content_type() == "text/html":
                                email_data.html_body = part.get_payload(decode=True).decode(part.get_content_charset())
                            elif part.get_content_disposition() == "attachment":
                                attachment_data = part.get_payload(decode=True)
                                attachment_name = part.get_filename()
                                attachment_base64 = base64.b64encode(attachment_data).decode("utf-8")
                                attachment_data_uri = (
                                    f"data:{part.get_content_type()};name={attachment_name};base64,{attachment_base64}"
                                )
                                objref = self._upload_asset_from_url(
                                    attachment_data_uri, attachment_name, part.get_content_type()
                                ).objref
                                email_data.attachments.append(objref)
                    else:
                        content_type = msg.get_content_type()
                        if content_type == "text/plain":
                            email_data.text_body = msg.get_payload(decode=True).decode(msg.get_content_charset())
                        elif content_type == "text/html":
                            email_data.html_body = msg.get_payload(decode=True).decode(msg.get_content_charset())

                    if email_data.html_body:
                        from bs4 import BeautifulSoup

                        soup = BeautifulSoup(email_data.html_body, "html.parser")
                        email_data.html_body_text = soup.get_text()
                    email_data.body = email_data.text_body or email_data.html_body_text
                    results.append(email_data)

        async_to_sync(self._output_stream.write)(EmailSearchOutput(results=results))
        output = self._output_stream.finalize()
        return output
