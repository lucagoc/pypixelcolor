# Getting Started

Welcome to the pypixelcolor wiki! This wiki provides documentation and guides on how to use the pypixelcolor library for controlling iPixel Color Bluetooth LED devices.

## Getting started with CLI

Find your device's MAC address by scanning for nearby Bluetooth devices:

```bash
pypixelcolor --scan
```

If your device is found, take note of its MAC address (e.g., `30:E1:AF:BD:5F:D0`).

```txt
% pypixelcolor --scan
ℹ️ [2025-11-18 21:07:35] [pypixelcolor.cli] Scanning for Bluetooth devices...
ℹ️ [2025-11-18 21:07:40] [pypixelcolor.cli] Found 1 device(s):
ℹ️ [2025-11-18 21:07:40] [pypixelcolor.cli]   - LED_BLE_E1BD5C80 (30:E1:AF:BD:5F:D0)
```

> If your device is not found, ensure it is powered, in range and not connected to another device.

To send a text message to your device, use the following command, replacing the MAC address with your device's MAC address:

```bash
pypixelcolor -a <MAC_ADDRESS> -c send_text "Hello pypixelcolor"
```

You can also add optional parameters to customize the display:

```bash
pypixelcolor -a <MAC_ADDRESS> -c send_text "Hello pypixelcolor" animation=1 speed=100
```

You can execute multiple commands in a single call. For example, to clear the display, set the brightness to 0, and switch to clock mode, you can run:

```bash
pypixelcolor -a <MAC_ADDRESS> -c clear -c set_brightness 0 -c set_clock_mode
```

For more information on available commands, refer to the [Commands](https://github.com/lucagoc/pypixelcolor/wiki/Commands) page.

## Running WebSocket Server

A WebSocket server is included to allow real-time control of your device. To start the server, use the following command:

```bash
python -m pypixelcolor.websocket -a <MAC_ADDRESS>
```

By default, the server listens on `localhost:4444`. You can specify a different host and port using the `--host` and `--port` options:

```bash
python -m pypixelcolor.websocket -a <MAC_ADDRESS> --host 0.0.0.0 --port 4444
```

Using a WebSocket client (for example, [WebSocket King](https://websocketking.com/)), and connect to the server at the specified host and port (by default `ws://localhost:4444`).
Once connected, you can send commands in JSON format. For example, to send a text message with animation and speed settings, you can use the following JSON payload:

```json
{
  "command": "send_text",
  "params": [
    "text=Hello from WebSocket",
    "animation=1",
    "speed=100"
  ]
}
```

For more information on available commands, refer to the [Commands](https://github.com/lucagoc/pypixelcolor/wiki/Commands) page.

## Using pypixelcolor as a Library

You can also use `pypixelcolor` as a Python library in your own scripts.

```python
import pypixelcolor

# Create a PixelColor device instance
device = pypixelcolor.Client("30:E1:AF:BD:5F:D0")

# Connect to the device
device.connect()

# Send a text message to the device
device.send_text("Hello from Python!", animation=1, speed=100)

# Disconnect from the device
device.disconnect()
```

You can connect to multiple devices by creating multiple `Client` instances:

```python
import pypixelcolor

devices = [
    pypixelcolor.Client("30:E1:AF:BD:5F:D0"), 
    pypixelcolor.Client("30:E1:AF:BD:20:A9")
]

for device in devices:
    device.connect()

for device in devices:
    device.send_text("Hello from Python!", animation=1, speed=100)

for device in devices:
    device.disconnect()
```

You can send commands to multiple iPixel Color devices concurrently using asynchronous programming with the `asyncio` library. Below is an example of how to achieve this:

```python
import asyncio
import pypixelcolor

async def main():
    addresses = [
        "30:E1:AF:BD:5F:D0",
        "30:E1:AF:BD:20:A9",
    ]

    # Create clients and connect sequentially (safe for common backends)
    devices = []
    for addr in addresses:
        client = pypixelcolor.AsyncClient(addr)
        await client.connect()
        devices.append(client)

    if not devices:
        return

    # Launch sends concurrently across all connected devices
    tasks = [asyncio.create_task(d.send_image("./python.png")) for d in devices]
    await asyncio.gather(*tasks)

    # Disconnect all
    for d in devices:
        await d.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

> ⚠️ Heavy data operations (like image sending) are not stable when performed concurrently on multiple devices due to potential Bluetooth backend limitations.
