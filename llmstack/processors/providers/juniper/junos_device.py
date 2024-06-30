from enum import Enum
from typing import Optional

from asgiref.sync import async_to_sync
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from pydantic import Field

from llmstack.processors.providers.api_processor_interface import (
    ApiProcessorInterface,
    ApiProcessorSchema,
)


class JunosCommandType(str, Enum):
    OPERATIONAL = "Operational"
    CONFIGURATION = "Configuration"

    def __str__(self):
        return self.value


class JunosDeviceConfiguration(ApiProcessorSchema):
    connection_id: str = Field(
        description="Junos login connection to use",
        json_schema_extra={"advanced_parameter": False, "widget": "connection"},
    )


class JunosDeviceInput(ApiProcessorSchema):
    command: str = Field(default="", description="Command to run")
    type: JunosCommandType = Field(
        default=JunosCommandType.OPERATIONAL,
        description="Type of command (operational/configuration) to run",
    )
    device_address: Optional[str] = Field(
        default=None,
        description="Address of the device. Uses the device from connection if not specified.",
    )


class JunosDeviceOutput(ApiProcessorSchema):
    output: str = Field(default="", description="Output of the command")


class JunosDevice(
    ApiProcessorInterface[JunosDeviceInput, JunosDeviceOutput, JunosDeviceConfiguration],
):
    """
    Text summarizer API processor
    """

    @staticmethod
    def name() -> str:
        return "Junos Device"

    @staticmethod
    def slug() -> str:
        return "junos_device"

    @staticmethod
    def description() -> str:
        return "Run commands and make configuration changes with set commands on a Junos device"

    @staticmethod
    def provider_slug() -> str:
        return "juniper"

    def process(self) -> dict:
        output_stream = self._output_stream
        command = self._input.command
        connection_configuration = self._env["connections"][self._config.connection_id]["configuration"]

        device = Device(
            host=self._input.device_address or connection_configuration["address"],
            user=connection_configuration["username"],
            password=connection_configuration["password"],
        ).open()

        if self._input.type == JunosCommandType.OPERATIONAL:
            output = device.cli(command, warning=False)
        else:
            with Config(device, mode="private") as cu:
                cu.load(command, format="set")
                cu.commit()
                output = "Configuration committed"

        async_to_sync(output_stream.write)(
            JunosDeviceOutput(
                output=output,
            ),
        )

        output = output_stream.finalize()
        device.close()

        return output
