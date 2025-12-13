# Using pypixelcolor as a Python library

## Basic Usage

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

## Multiple Devices

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

### Asynchronous Usage

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

!!! warning "Caution"
    Heavy data operations (like image sending) are not stable when performed concurrently on multiple devices due to potential Bluetooth backend limitations.
