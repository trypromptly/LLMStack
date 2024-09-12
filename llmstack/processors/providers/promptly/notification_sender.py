import base64
import logging
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Literal, Optional, Union

import sendgrid
from asgiref.sync import async_to_sync
from pydantic import BaseModel, Field

from llmstack.apps.schemas import OutputTemplate
from llmstack.assets.utils import get_asset_by_objref_internal
from llmstack.common.blocks.base.processor import Schema
from llmstack.common.utils.utils import validate_parse_data_uri
from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface
from llmstack.processors.providers.metrics import MetricType
from llmstack.processors.providers.promptly import SendgridEmailSenderConfig

logger = logging.getLogger(__name__)


class EmailProvider(BaseModel):
    type: Literal["Email"] = "Email"


NotificationProvider = Union[EmailProvider]


class NotificationSenderInput(Schema):
    subject: Optional[str] = Field(default=None, description="Subject of the notifcation")
    text_body: Optional[str] = Field(default=None, json_schema_extra={"widget": "textarea"})
    html_body: Optional[str] = Field(default=None, json_schema_extra={"widget": "textarea"})
    attachments: Optional[List[str]] = Field(default=[], description="Email Attachments")


class NotificationSenderConfigurations(Schema):
    notification_provider: NotificationProvider = Field(
        default=EmailProvider(),
        description="Notification provider to use",
        json_schema_extra={"advanced_parameter": False},
    )


class NotificationSenderOutput(Schema):
    code: int = Field(description="Status code of the email send")


def send_email_via_platform_email_sender(recipients, subject, text_content, html_content, attachments, provider_config):
    if provider_config:
        if isinstance(provider_config, SendgridEmailSenderConfig):
            if subject is None:
                subject = "Notification Promptly"
            sendgrid_client = sendgrid.SendGridAPIClient(api_key=provider_config.api_key)
            message = sendgrid.Mail(
                from_email=provider_config.from_email,
                to_emails=recipients,
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
            result = sendgrid_client.send(message)
            return result.status_code


class NotificationSenderProcessor(
    ApiProcessorInterface[NotificationSenderInput, NotificationSenderOutput, NotificationSenderConfigurations]
):
    @staticmethod
    def name() -> str:
        return "Notification Sender"

    @staticmethod
    def slug() -> str:
        return "notification_sender"

    @staticmethod
    def description() -> str:
        return "Send a notification to the user"

    @staticmethod
    def provider_slug() -> str:
        return "promptly"

    @classmethod
    def get_output_template(cls) -> OutputTemplate | None:
        return OutputTemplate(markdown="{{code}}", jsonpath="$.code")

    def process(self) -> dict:
        text_content = self._input.text_body
        html_content = self._input.html_body
        subject = self._input.subject
        attachment_data_uris = []
        if self._input.attachments:
            for attachment in self._input.attachments:
                if attachment.startswith("objref://"):
                    attachment_data_uris.append(get_asset_by_objref_internal(attachment))

        if isinstance(self._config.notification_provider, EmailProvider):
            provider_config = self.get_provider_config(provider_slug="promptly")
            recipient_emails = self._request.user.email

            email_msg = MIMEMultipart()
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

            status = send_email_via_platform_email_sender(
                recipients=recipient_emails,
                subject=subject,
                text_content=text_content,
                html_content=html_content,
                attachments=attachment_data_uris,
                provider_config=provider_config.email_sender,
            )
            if status >= 200 and status < 300:
                self._usage_data.append(
                    (
                        f"{self.provider_slug()}/{self.slug()}/email/*",
                        MetricType.API_INVOCATION,
                        (provider_config.provider_config_source, 1),
                    )
                )

            async_to_sync(self._output_stream.write)(NotificationSenderOutput(code=status))

        output = self._output_stream.finalize()
        return output
