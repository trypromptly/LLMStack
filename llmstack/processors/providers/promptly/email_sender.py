import base64
import imaplib
import smtplib
import time
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Literal, Optional, Union

from asgiref.sync import async_to_sync
from pydantic import BaseModel, Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.assets.utils import get_asset_by_objref_internal
from llmstack.common.blocks.base.processor import Schema
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface


class GmailEmailProvider(BaseModel):
    type: Literal["gmail"] = "gmail"


class OutlookEmailProvider(BaseModel):
    type: Literal["outlook"] = "outlook"


class YahooEmailProvider(BaseModel):
    type: Literal["yahoo"] = "yahoo"


EmailProvider = Union[GmailEmailProvider, OutlookEmailProvider, YahooEmailProvider]


class EmailSenderInput(Schema):
    recipient_email: List[str] = Field(default=[], description="Recipient email")
    sender_name: Optional[str] = Field(default=None, description="Sender name")
    subject: str = Field(description="Subject of the email")
    text_body: Optional[str] = Field(default=None, json_schema_extra={"widget": "textarea"})
    html_body: Optional[str] = Field(default=None, json_schema_extra={"widget": "textarea"})
    attachments: Optional[List[str]] = Field(default=[], description="Email Attachments")
    orignal_message_id: Optional[str] = Field(default=None, description="Mail Id that is being replied to")


class EmailSenderConfigurations(Schema):
    email_provider: EmailProvider = Field(
        default=GmailEmailProvider(),
        description="Email provider to use",
        json_schema_extra={"advanced_parameter": False},
    )
    use_bcc: bool = Field(
        default=False,
        description="Use BCC to send the email",
    )
    create_draft: bool = Field(
        default=True,
        description="Create a draft email",
    )
    connection_id: Optional[str] = Field(
        default=None,
        json_schema_extra={"widget": "connection", "advanced_parameter": False},
        description="Use your authenticated connection to make the request",
    )


class EmailSenderOutput(Schema):
    code: int = Field(description="Status code of the email send")


def create_email_draft_via_gmail(smtp_username, smtp_password, recipients, msg):
    msg_str = msg.as_string()
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(smtp_username, smtp_password)
    mail.select('"[Gmail]/Drafts"')
    # Append the message to the 'Drafts' folder
    mail.append('"[Gmail]/Drafts"', "", imaplib.Time2Internaldate(time.time()), msg_str.encode("utf-8"))
    mail.logout()


def send_email_via_gmail(recipients, msg, smtp_username, smtp_password):
    smtp_server = "smtp.gmail.com"
    port = 587  # For TLS
    msg["From"] = smtp_username

    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls()  # Upgrade the connection to a secure encrypted SSL/TLS connection
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, recipients, msg.as_string())


def create_email_draft_via_outlook(smtp_username, smtp_password, recipients, msg):
    raise NotImplementedError("Outlook does not support creating email drafts")


def send_email_via_outlook(recipients, msg, smtp_username, smtp_password):
    smtp_server = "smtp.outlook.com"
    port = 587  # For TLS
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls()  # Upgrade the connection to a secure encrypted SSL/TLS connection
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, recipients, msg.as_string())


def create_email_draft_via_yahoo(smtp_username, smtp_password, recipients, msg):
    raise NotImplementedError("Yahoo does not support creating email drafts")


def send_email_via_yahoo(recipients, msg, smtp_username, smtp_password):
    smtp_server = "smtp.mail.yahoo.com"
    port = 587  # For TLS
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, recipients, msg.as_string())


class EmailSenderProcessor(ApiProcessorInterface[EmailSenderInput, EmailSenderOutput, EmailSenderConfigurations]):
    @staticmethod
    def name() -> str:
        return "Email Sender"

    @staticmethod
    def slug() -> str:
        return "email_sender"

    @staticmethod
    def description() -> str:
        return "Send an email"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    @classmethod
    def get_output_template(cls) -> OutputTemplate | None:
        return OutputTemplate(markdown="{{code}}")

    def process(self) -> dict:
        text_content = self._input.text_body
        html_content = self._input.html_body
        subject = self._input.subject
        recipient_emails = ", ".join(self._input.recipient_email)
        attachment_data_uris = []

        if self._input.attachments:
            for attachment in self._input.attachments:
                if attachment.startswith("objref://"):
                    attachment_data_uris.append(get_asset_by_objref_internal(attachment))

        email_msg = MIMEMultipart()

        if not self._config.use_bcc:
            email_msg["To"] = recipient_emails
        email_msg["Subject"] = subject

        if self._input.orignal_message_id:
            # This is a reply email
            email_msg["In-Reply-To"] = self._input.orignal_message_id
            email_msg["References"] = self._input.orignal_message_id

        if text_content:
            email_msg.attach(MIMEText(text_content, "plain"))

        if html_content:
            email_msg.attach(MIMEText(html_content, "html"))

        for attachment in attachment_data_uris:
            mime_type, file_name, b64_encoded_data = validate_parse_data_uri(attachment)
            data_bytes = base64.b64decode(b64_encoded_data)
            part = MIMEBase("application", mime_type)
            part.set_payload(data_bytes)
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={file_name}")
            email_msg.attach(part)

        connection = self._env["connections"][self._config.connection_id]["configuration"]

        if isinstance(self._config.email_provider, GmailEmailProvider):
            if self._config.create_draft:
                create_email_draft_via_gmail(
                    recipients=self._input.recipient_email,
                    msg=email_msg,
                    smtp_username=connection["username"],
                    smtp_password=connection["password"],
                )
            else:
                send_email_via_gmail(
                    recipients=self._input.recipient_email,
                    msg=email_msg,
                    smtp_username=connection["username"],
                    smtp_password=connection["password"],
                )
        elif isinstance(self._config.email_provider, OutlookEmailProvider):
            send_email_via_outlook(
                recipients=self._input.recipient_email,
                msg=email_msg,
                smtp_username=connection["username"],
                smtp_password=connection["password"],
            )
        elif isinstance(self._config.email_provider, YahooEmailProvider):
            send_email_via_yahoo(
                recipients=self._input.recipient_email,
                msg=email_msg,
                smtp_username=connection["username"],
                smtp_password=connection["password"],
            )

        async_to_sync(self._output_stream.write)(EmailSenderOutput(code=200))

        output = self._output_stream.finalize()
        return output
