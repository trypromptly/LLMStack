import base64
import smtplib
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
from llmstack.processors.providers.promptly import SendgridEmailSenderConfig


class GmailEmailProvider(BaseModel):
    type: Literal["gmail"] = "gmail"


class OutlookEmailProvider(BaseModel):
    type: Literal["outlook"] = "outlook"


class YahooEmailProvider(BaseModel):
    type: Literal["yahoo"] = "yahoo"


class PlatformEmailSenderProvider(BaseModel):
    type: Literal["platform_email_sender"] = "platform_email_sender"
    deployment_name: str = Field(
        title="Deployment Name",
        description="Deployment name of the platform email sender",
        default="*",
        json_schema_extra={"advanced_parameter": False},
    )


EmailProvider = Union[GmailEmailProvider, OutlookEmailProvider, YahooEmailProvider, PlatformEmailSenderProvider]


class EmailSenderInput(Schema):
    recipient_email: List[str] = Field(default=[], description="Recipient email")
    subject: str = Field(description="Subject of the email")
    text_body: Optional[str] = Field(default=None, json_schema_extra={"widget": "textarea"})
    html_body: Optional[str] = Field(default=None, json_schema_extra={"widget": "textarea"})
    attachments: Optional[List[str]] = Field(default=[], description="Email Attachments")


class EmailSenderConfigurations(Schema):
    email_provider: EmailProvider = Field(
        default=PlatformEmailSenderProvider(),
        description="Email provider to use",
        json_schema_extra={"advanced_parameter": False},
    )
    use_bcc: bool = Field(
        default=False,
        description="Use BCC to send the email",
    )
    connection_id: Optional[str] = Field(
        default=None,
        json_schema_extra={"widget": "connection"},
        description="Use your authenticated connection to make the request",
    )


class EmailSenderOutput(Schema):
    code: int


def send_email_via_gmail(recipients, msg, smtp_username, smtp_password):
    smtp_server = "smtp.gmail.com"
    port = 587  # For TLS
    msg["From"] = smtp_username

    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls()  # Upgrade the connection to a secure encrypted SSL/TLS connection
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, recipients, msg.as_string())


def send_email_via_outlook(recipients, msg, smtp_username, smtp_password):
    smtp_server = "smtp.outlook.com"
    port = 587  # For TLS
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls()  # Upgrade the connection to a secure encrypted SSL/TLS connection
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, recipients, msg.as_string())


def send_email_via_yahoo(recipients, msg, smtp_username, smtp_password):
    smtp_server = "smtp.mail.yahoo.com"
    port = 587  # For TLS
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, recipients, msg.as_string())


def send_email_via_platform_email_sender(recipients, subject, text_content, html_content, attachments, provider_config):
    if provider_config:
        if isinstance(provider_config, SendgridEmailSenderConfig):
            import sendgrid

            sendgrid_client = sendgrid.SendGridAPIClient(api_key=provider_config.api_key)
            message = sendgrid.Mail(
                from_email=provider_config.from_email,
                to_email=recipients,
                subject=subject,
                plain_text_content=text_content,
                html_content=html_content,
            )
            if attachments:
                for attachment in attachments:
                    mime_type, file_name, b64_encoded_data = validate_parse_data_uri(attachment)
                    data_bytes = base64.b64decode(b64_encoded_data)
                    message.add_attachment(
                        sendgrid.Attachment(
                            file_content=data_bytes, file_name=file_name, file_type=mime_type, disposition="attachment"
                        )
                    )
            sendgrid_client.send(message)


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

        if isinstance(self._config.email_provider, PlatformEmailSenderProvider):
            provider_config = self.get_provider_config(deployment_key=self._config.email_provider.deployment_name)
            send_email_via_platform_email_sender(
                recipients=recipient_emails,
                subject=subject,
                text_content=text_content,
                html_content=html_content,
                attachments=attachment_data_uris,
                provider_config=provider_config,
            )
        else:
            email_msg = MIMEMultipart()

            if not self._config.use_bcc:
                email_msg["To"] = recipient_emails
            email_msg["Subject"] = subject

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
