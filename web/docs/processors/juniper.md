---
id: juniper
title: Juniper
---

The `Juniper` provider includes processors that allows you to interact with a Juniper device, pull data from it, and execute commands on it.

## Junos Device

### Input

- `command`: The command to execute on the Juniper device.
- `type`: The type of command to execute. Can be `Operational` or `Configuration`.
- `device_address`: Optional IP address of the Juniper device to connect to. If not provided, the device address will be retrieved from the connection in configuration.

### Configuration

- `connection_id`: The connection ID of the Juniper device to use. Add a connection of type `Junos Login` from Settings > Connections, add your device address, username, and password, and test the connection.

### Output

- `output`: The output of the command executed on the Juniper device.
